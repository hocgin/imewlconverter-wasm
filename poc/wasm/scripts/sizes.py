from pathlib import Path
import json,gzip,hashlib
root=Path(__file__).resolve().parents[1]
publish=root.parents[1]/'artifacts/publish/wwwroot'
files=list(publish.rglob('*'));files=[p for p in files if p.is_file()]
framework=[p for p in files if p.parent.name=='_framework' and p.suffix not in ('.gz','.br')]
r={'publishTotalBytesIncludingCompressionVariants':sum(p.stat().st_size for p in files),'frameworkUncompressedBytes':sum(p.stat().st_size for p in framework),'frameworkGzipBytes':sum(len(gzip.compress(p.read_bytes())) for p in framework),'files':len(files)}
(root/'reports/artifact-sizes.json').write_text(json.dumps(r,indent=2));print(r)
