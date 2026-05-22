"""clean — (stretch) bulk terminate resources matching a tag.

WARNING — DESIGN-FOR-SAFETY
---------------------------
This is the most dangerous command in the CLI. Get the contract right:

  1. DEFAULT IS DRY-RUN. Without --apply the command MUST NOT touch resources.
     It only lists what WOULD be deleted.
  2. Even with --apply, you should consider printing a summary count first
     ("about to terminate N EC2 + M volumes — proceed?"), though for this
     starter a hard `--apply` flag is enough.
  3. Never use this with a tag you don't fully own. Reflection prompt in
     README covers the blast-radius scenario.

WHAT YOU MUST BUILD
-------------------
1. `_find_targets(tag_key, tag_val)` — return a dict like:
     {"ec2": [<instance ids in non-terminal state>],
      "volume": [<volume ids in 'available' state only>]}
   Skip terminated/shutting-down instances (already gone).
   Skip in-use volumes (can't delete while attached — would error anyway).

2. `run(args)` — call _find_targets, print the plan, then either:
     - bail with "(dry-run — pass --apply to ...)"  (default)
     - or actually terminate (when --apply)

HELPERS YOU CAN USE
-------------------
From commands._common:
  parse_kv(s) -> (k, v)

AWS APIS YOU'LL NEED
--------------------
- ec2.describe_instances() + describe_volumes() — same as list_cmd
- ec2.terminate_instances(InstanceIds=[...])
- ec2.delete_volume(VolumeId=...)  (per volume, no bulk API)

VERIFY
------
    pytest tests/test_clean.py -v
"""

import boto3

from commands._common import parse_kv, tags_to_dict


def _find_targets(tag_key, tag_val):
    """Return {"ec2": [...], "volume": [...]} matching tag in non-terminal state."""
    ec2 = boto3.client("ec2")
    targets = {"ec2": [], "volume": []}

    # Find EC2
    paginator = ec2.get_paginator("describe_instances")
    for page in paginator.paginate():
        for res in page["Reservations"]:
            for inst in res["Instances"]:
                # Don't target already dead ones
                if inst["State"]["Name"] in ["terminated", "shutting-down"]:
                    continue
                tags = tags_to_dict(inst.get("Tags", []))
                if tags.get(tag_key) == tag_val:
                    targets["ec2"].append(inst["InstanceId"])

    # Find Volumes
    vol_paginator = ec2.get_paginator("describe_volumes")
    for page in vol_paginator.paginate():
        for vol in page["Volumes"]:
            if vol["State"] == "deleted":
                continue
            tags = tags_to_dict(vol.get("Tags", []))
            if tags.get(tag_key) == tag_val:
                targets["volume"].append(vol["VolumeId"])

        return targets


def run(args):
    """Entry point.

    Args set by argparse:
        args.tag    — "key=value" string (REQUIRED)
        args.apply  — bool, must be True to actually delete (default False = dry-run)
    """
    k, v = parse_kv(args.tag)
    targets = _find_targets(k, v)
    total = len(targets["ec2"]) + len(targets["volume"])

    # 1. Handle "No matches" case
    if total == 0:
        print("Nothing to clean.")
        return

    print(f"Found {total} resources with {k}={v}")

    # 2. Handle Dry-run
    if not args.apply:
        # Must include the word "dry-run"
        print(f"This is a dry-run. Use --apply to actually delete.")
        for res_type, ids in targets.items():
            for rid in ids:
                print(f"  Would terminate {res_type}: {rid}")
        return

    # 3. Apply deletion
    from commands.terminate_cmd import _terminate_ec2

    for rid in targets["ec2"]:
        _terminate_ec2(rid, force=True)
        print(f"Terminated ec2: {rid}")
