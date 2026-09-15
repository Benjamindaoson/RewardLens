# Phase II V2 manual GQA/VG image delivery

The frozen acquisition list is /root/autodl-fs/RewardLens/phase2_v2_sources/required_gqa_image_ids.txt.
Its required SHA-256 is 734b95bde39f110f7734ed9dca12972a13a17cdd569c8e7108a7f8010616fbeb (58,851 IDs). Do not regenerate or edit it.

The repository tool rewardlens/scripts/phase2_image_handoff.py uses only Python's standard library. It does not download, transform, decode, re-encode, or select images.

## Extract raw JPEG bytes from a delivered archive

Use a complete, official images.zip or an extracted directory. Keep the output directory separate from the source and receipt:

    cd /root/autodl-tmp/RewardLens/code
    PYTHONPATH=rewardlens /root/autodl-tmp/RewardLens/venv/bin/python \
      rewardlens/scripts/phase2_image_handoff.py extract \
      --required-ids /root/autodl-fs/RewardLens/phase2_v2_sources/required_gqa_image_ids.txt \
      --images /MANUAL_DELIVERY/images.zip \
      --output-dir /root/autodl-fs/RewardLens/phase2_v2_sources/gqa/required_raw_images \
      --receipt /root/autodl-fs/RewardLens/phase2_v2_sources/gqa/manual_delivery_extract_receipt.json

For a ZIP, extraction first runs ZipFile.testzip() and fails on any corrupt member. Only required numeric .jpg members are copied byte-for-byte. If a required output file already exists, its raw-byte SHA-256 must match the source member or the command fails.

## Verify an extracted delivery

    cd /root/autodl-tmp/RewardLens/code
    PYTHONPATH=rewardlens /root/autodl-tmp/RewardLens/venv/bin/python \
      rewardlens/scripts/phase2_image_handoff.py verify \
      --required-ids /root/autodl-fs/RewardLens/phase2_v2_sources/required_gqa_image_ids.txt \
      --images /root/autodl-fs/RewardLens/phase2_v2_sources/gqa/required_raw_images \
      --receipt /root/autodl-fs/RewardLens/phase2_v2_sources/gqa/manual_delivery_verification.json

Both receipts are atomically published JSON and include the required, found, and missing IDs; duplicate raw-byte SHA-256 groups; unexpected files; and a per-image raw-byte SHA-256 manifest with byte count and relative path. The extract receipt additionally records its source and output directory.

A nonempty missing_ids, duplicate_physical_sha256, or unexpected_files field is a receipt finding, not a split-selection decision. Do not repair the downstream split or start inference until the delivery receipt is reviewed.

## Separate TallyQA Count dependency

The frozen Count eligibility universe includes COCO-backed items: 49,616 unique COCO image IDs across 100,049 eligible TallyQA Count question rows. Their raw bytes remain required for complete physical-SHA256 identity, collision repair, and final leakage preflight. They are not part of the frozen 58,851 GQA/VG list and are not silently excluded by this tooling.

## COCO-backed TallyQA Count delivery

The separately frozen COCO list is /root/autodl-fs/RewardLens/phase2_v2_sources/required_coco_image_ids.txt. Its receipt supplies the exact path-derived expected_canonical_filename_by_id mapping. COCO image IDs alone are not used to infer a split.

Run extraction once for each delivered official archive into the same output directory, retaining distinct receipts:

    cd /root/autodl-tmp/RewardLens/code
    PYTHONPATH=rewardlens /root/autodl-tmp/RewardLens/venv/bin/python \
      rewardlens/scripts/phase2_image_handoff.py extract \
      --required-ids /root/autodl-fs/RewardLens/phase2_v2_sources/required_coco_image_ids.txt \
      --filename-manifest /root/autodl-fs/RewardLens/phase2_v2_sources/required_coco_image_ids_receipt.json \
      --images /MANUAL_DELIVERY/train2014.zip \
      --output-dir /root/autodl-fs/RewardLens/phase2_v2_sources/coco/required_raw_images \
      --receipt /root/autodl-fs/RewardLens/phase2_v2_sources/coco/train2014_extract_receipt.json

    PYTHONPATH=rewardlens /root/autodl-tmp/RewardLens/venv/bin/python \
      rewardlens/scripts/phase2_image_handoff.py extract \
      --required-ids /root/autodl-fs/RewardLens/phase2_v2_sources/required_coco_image_ids.txt \
      --filename-manifest /root/autodl-fs/RewardLens/phase2_v2_sources/required_coco_image_ids_receipt.json \
      --images /MANUAL_DELIVERY/val2014.zip \
      --output-dir /root/autodl-fs/RewardLens/phase2_v2_sources/coco/required_raw_images \
      --receipt /root/autodl-fs/RewardLens/phase2_v2_sources/coco/val2014_extract_receipt.json

Then run the same verify command with --filename-manifest and the combined output directory. The intermediate archive receipts will show the IDs belonging to the other split as missing; only the combined final verification receipt is the full-delivery gate.
