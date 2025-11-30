import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATCHES = {
    "whatsapp_bot/job_and_listener/job/core.py": [
        # remove CreateJob import line
        (re.compile(r"^(\s*)from\s+classes\s+import\s+CreateJob\s*$", re.M), ""),
        # replace CreateJob.delete_job(...) call
        (re.compile(r"CreateJob\.delete_job\s*\(\s*scheduler\s*,\s*cur\s*,\s*job_id\s*\)"), "delete_job(scheduler, cur, job_id)"),
    ],
    "whatsapp_bot/mass_messages.py": [
        # replace import
        (re.compile(r"^(\s*)from\s+classes\s+import\s+CreateJob\s*$", re.M),
         "from job_and_listener.job.core import create_job, JobMetadata, JobAction, JobSchedule"),
        # replace the specific CreateJob(...) block used in mass_messages (multi-line)
        (re.compile(
            r"CreateJob\(\s*cur\s*=\s*cur\s*,\s*scheduler\s*=\s*scheduler\s*,\s*id\s*=\s*\"send_message_to_\".*?misfire_grace_time\s*=\s*1\s*.*?\)",
            re.S),
         "metadata = JobMetadata(id=f\"send_message_to_{p}_{run_time.strftime('%Y%m%d%H%M%S')}\", description=\"\", batch_id=\"send_mass_messages_batch\")\n        action = JobAction(func=mass_messages_job, other_args={\"message\": message, \"p\": p})\n        schedule = JobSchedule(run_time=run_time, coalesce=True, misfire_grace_time=1)\n        create_job(cur, scheduler, metadata, action, schedule)"),
    ],
    "whatsapp_bot/api/routes/test_routes.py": [
        (re.compile(r"^(\s*)from\s+classes\s+import\s+CreateJob\s*$", re.M),
         "from job_and_listener.job.core import create_job, JobMetadata, JobAction, JobSchedule, delete_job"),
        (re.compile(r"CreateJob\(\s*cur\s*=\s*cur\s*,\s*scheduler\s*=\s*scheduler\s*,\s*id\s*=\s*\"test-job-1\".*?\)", re.S),
         "metadata = JobMetadata(id=\"test-job-1\", description=\"test job\", batch_id=\"tests\")\n    action = JobAction(func=test_job_func, other_args={\"x\": 1})\n    schedule = JobSchedule(run_time=run_time)\n    create_job(cur, scheduler, metadata, action, schedule)"),
        (re.compile(r"CreateJob\(\s*cur\s*=\s*cur\s*,\s*scheduler\s*=\s*scheduler\s*,\s*id\s*=\s*\"test-job-2\".*?\)", re.S),
         "metadata = JobMetadata(id=\"test-job-2\", description=\"another test\", batch_id=\"tests\")\n    action = JobAction(func=test_job_func2, other_args={\"y\": 2})\n    schedule = JobSchedule(run_time=run_time2)\n    create_job(cur, scheduler, metadata, action, schedule)"),
    ],
    "whatsapp_bot/mavdak/mavdak_end.py": [
        (re.compile(r"^(\s*)from\s+classes\s+import\s+CreateJob\s*$", re.M),
         "from job_and_listener.job.core import create_job, JobMetadata, JobAction, JobSchedule"),
        (re.compile(r"CreateJob\(\s*cur\s*=\s*cur\s*,\s*scheduler\s*=\s*scheduler\s*,\s*id\s*=\s*f\"mavdak_end_\{participant\.id\}_\{run_time\.strftime\('%Y%m%d%H%M%S'\)\}\".*?\)", re.S),
         "metadata = JobMetadata(id=f\"mavdak_end_{participant.id}_{run_time.strftime('%Y%m%d%H%M%S')}\", description=\"mavdak end notify\", batch_id=\"mavdak_end_batch\")\n    action = JobAction(func=mavdak_notify_job, other_args={\"participant_id\": participant.id})\n    schedule = JobSchedule(run_time=run_time)\n    create_job(cur, scheduler, metadata, action, schedule)"),
    ],
    "whatsapp_bot/schedule_create_group.py": [
        (re.compile(r"^(\s*)from\s+classes\s+import\s+CreateJob\s*,\s*JobInfo\s*,\s*WhatsappGroupCreate\s*$", re.M),
         "from job_and_listener.job.core import create_job, JobMetadata, JobAction, JobSchedule\nfrom classes import JobInfo, WhatsappGroupCreate"),
        (re.compile(r"job\s*=\s*CreateJob\(\s*cur\s*=\s*cur\s*,\s*scheduler\s*=\s*scheduler\s*,\s*id\s*=\s*job_id\s*,\s*description\s*=\s*job_info\.description.*?\)", re.S),
         "metadata = JobMetadata(id=job_id, description=job_info.description, batch_id=batch_name)\n    action = JobAction(func=job_info.function, other_args=job_info.args)\n    schedule = JobSchedule(run_time=job_info.run_time)\n    create_job(cur, scheduler, metadata, action, schedule)"),
        (re.compile(r"CreateJob\(\s*func\s*=\s*job_info\.function\s*,\s*id\s*=\s*job_info\.id\s*,\s*run_time\s*=\s*job_info\.run_time.*?\)", re.S),
         "metadata = JobMetadata(id=job_info.id, description=job_info.description, batch_id=batch_name)\n        action = JobAction(func=job_info.function, other_args=job_info.args)\n        schedule = JobSchedule(run_time=job_info.run_time)\n        create_job(cur, scheduler, metadata, action, schedule)"),
    ],
}

def apply_patches():
    for rel, repls in PATCHES.items():
        path = ROOT / rel
        if not path.exists():
            print(f"Missing file: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        new_text = text
        applied = False
        for pattern, repl in repls:
            new_text, count = pattern.subn(repl, new_text)
            if count:
                print(f"Applied {count} replacement(s) in {rel}")
                applied = True
        if applied:
            bak = path.with_suffix(path.suffix + ".bak")
            if not bak.exists():
                shutil.copy2(path, bak)
            path.write_text(new_text, encoding="utf-8")
            print(f"Patched {rel} (backup written to {bak.name})")
        else:
            print(f"No changes for {rel}")

if __name__ == "__main__":
    apply_patches()
