"""Read-only dashboard: resumed counts must not inflate measured throughput."""
import importlib.util
assert importlib.util.find_spec("scripts.phase2_live_dashboard"), "read-only worker dashboard not implemented"
from scripts.phase2_live_dashboard import measure,render

def check():
    data={"pid":10,"model":"synthetic","stage":"downstream","done":11200,"total":22400,
          "pools_completed":400,"pair_edges":11200,"static_completed":800,
          "elapsed_seconds":500,"abstention_rate":.01,"checkpoint":"JSONL fsync",
          "gpu":{"util_percent":80,"vram_mib":16000,"total_mib":81920}}
    first,base=measure(data,None,100)
    assert first["percent"]==50 and first["throughput_per_second"] is None
    current,base=measure({**data,"done":11480,"pair_edges":11480,"pools_completed":410},base,140)
    assert current["throughput_per_second"]==7 and current["eta_seconds"]==1560
    assert "410/800" in render(current) and "11480/22400" in render(current)
    assert "JSONL fsync" in render(current) and "16000" in render(current)
    assert "Abstention rate: 1.00%" in render(current)
    resumed,_=measure({**data,"pid":11,"done":20000},base,160)
    assert resumed["throughput_per_second"] is None
    audit,_=measure({**data,"stage":"audit","done":1200,"total":2400},base,180)
    assert audit["percent"]==50 and audit["throughput_per_second"] is None
    assert "1200/2400" in render(audit)
    import tempfile
    from pathlib import Path
    from unittest.mock import patch
    from scripts import phase2_live_dashboard as module
    from scripts.phase2_autonomous import write_json
    with tempfile.TemporaryDirectory() as directory,patch.object(module,"OUT",Path(directory)),patch.object(module,"gpu",return_value=data["gpu"]):
        root=Path(directory)
        write_json(root/"workers/017/status.json",{"stage":"running","model":"synthetic","pid":10})
        write_json(root/"synthetic/task_status.json",{"stage":"audit","pid":10,"completed":2400})
        write_json(root/"synthetic/execution/live_status.json",data)
        assert module.sample("017")["stage"]=="downstream", "stale audit status hid active phase2"
        write_json(root/"workers/017/status.json",{"stage":"running","model":"synthetic","pid":11})
        write_json(root/"synthetic/task_status.json",{"stage":"loading","pid":11})
        assert module.sample("017")["stage"]=="loading", "old PID status leaked across resume"
        write_json(root/"synthetic/task_status.json",{"stage":"audit","pid":11})
        unknown,base=measure(module.sample("017"),None,200)
        assert base is None and unknown["percent"] is None, "unknown resumed audit count became zero baseline"
        assert "N/A/2400" in render(unknown)
        write_json(root/"synthetic/task_status.json",{"stage":"audit","pid":11,"completed":2310})
        resumed,base=measure(module.sample("017"),base,210)
        assert resumed["throughput_per_second"] is None
        write_json(root/"synthetic/task_status.json",{"stage":"audit","pid":11,"completed":2320})
        advanced,_=measure(module.sample("017"),base,220)
        assert advanced["throughput_per_second"]==1 and advanced["eta_seconds"]==80
    with patch.object(Path,"exists",return_value=True),patch.object(Path,"read_text",side_effect=FileNotFoundError("status replaced during read")):
        assert module.read(Path("status.json"))=={}, "transient missing display source killed observer"
    print("READ_ONLY_DASHBOARD_RESUME_RATE_AND_STAGE_PASS")

if __name__=="__main__":
    check()
