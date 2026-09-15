from scripts.expanded_analysis import validate_rows,analyze_factor
from stats import FACTORS

def check():
    rows=[{"model_id":str(i),"family":str(i),"factor":"count","A":i/10,
           "PFC":(i%3)/4,"PSC":(i%4)/5,"U":0.2+i/20} for i in range(8)]
    result=analyze_factor(rows)
    assert result["n_models"]==8 and len(result["folds"])==8
    assert result["status"]=="ESTIMABLE"
    assert result["bootstrap"]["n_boot"]==1000
    short=analyze_factor(rows[:3])
    assert short["delta_mae"] is None and short["status"]=="NOT_IDENTIFIABLE"
    bad=[dict(r) for r in rows];bad[0]["A"]=None
    assert analyze_factor(bad)["status"]=="NOT_IDENTIFIABLE"
    full=[dict(r,factor=f) for r in rows for f in FACTORS]
    validate_rows(full)
    from scripts.expanded_analysis import analyses
    for row in full:
        row.update(U2=row["U"],U4=row["U"],U8=row["U"],decoder_family=row["family"])
    full[0]["A"]=None
    full[1]["PFC"]=None
    rq2,rq3,robustness,matched=analyses(full)
    assert rq2["8"]["count"]["status"]=="NOT_IDENTIFIABLE"
    assert matched["bands"]["count"]["status"]=="NOT_ESTIMABLE"
    try:
        validate_rows(full+[full[0]])
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate model-factor rows accepted")
    from scripts import expanded_analysis as runtime_module
    assert hasattr(runtime_module,"historical_audit_time"), "missing receipt/latency reconciliation"
    assert runtime_module.historical_audit_time(0,[{"latency_ms":1000},{"latency_ms":2000}])==(3.0,True)
    assert runtime_module.historical_audit_time(5,[{"latency_ms":1000},{"latency_ms":2000}])==(5.0,False)
    assert runtime_module.historical_audit_time(2,[{"latency_ms":3000}])==(3.0,True)
    # Execute the real table-emission block without requiring unfinished GPU results.
    # A model-wide count mistakenly emitted per factor must fail this check.
    import ast,inspect
    from scripts import expanded_analysis as module
    tree=ast.parse(inspect.getsource(module.collect))
    block=next(node for node in ast.walk(tree) if isinstance(node,ast.For) and isinstance(node.target,ast.Name) and node.target.id=="factor")
    namespace={"FACTORS":["count","attribute"],"model":"synthetic","family":"synthetic","decoder":"synthetic",
               "sm":[],"auditmetrics":[],"um":[{"factor":f,"N":n,"U":.5} for f in ("count","attribute") for n in (2,4,8)],
               "static":[{"factor":"count"}]*3+[{"factor":"attribute"}]*5,"factor_rows":[]}
    exec(compile(ast.Module(body=[block],type_ignores=[]),"<production table emission>","exec"),namespace)
    assert [r["n_static_completed"] for r in namespace["factor_rows"]]==[3,5], namespace["factor_rows"]
    print("EXPANDED_ANALYSIS_SYNTHETIC_AND_FACTOR_COUNTS_PASS")

if __name__=="__main__":
    check()
