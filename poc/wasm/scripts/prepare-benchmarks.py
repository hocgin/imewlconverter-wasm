# Real dictionary rows only; no repeated/padded synthetic data. Source was fetched separately.
from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parents[1];dest=root/'artifacts/fixtures';dest.mkdir(parents=True,exist_ok=True)
source=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/imewl-jichu.dict.yaml');data=source.read_bytes()
assert hashlib.sha256(data).hexdigest()=='38dc941a717d8c20f44843fed367b9603895088ed98d420185e9b05705a7748d', 'Source hash changed; record a new corpus before testing'
rows=[line+b'\n' for line in data.splitlines() if b'\t' in line and not line.startswith(b'#')]
manifest={'source':'https://raw.githubusercontent.com/amzxyz/rime-wanxiang/c36653e7c454bfb30f8e634054970d3abefa036c/dicts/jichu.dict.yaml','downloadedSHA256':hashlib.sha256(data).hexdigest(),'sourceBytes':len(data),'method':'prefix of complete original TSV entry rows; YAML header/comments omitted, no padding or repetition','fixtures':[]}
for target in [1_000_000,10_000_000,50_000_000]:
 selected=[];n=0
 for line in rows:
  if n+len(line)>target:break
  selected.append(line);n+=len(line)
 path=dest/f'real-{target//1_000_000}MB.dict.yaml';path.write_bytes(b''.join(selected))
 manifest['fixtures'].append({'path':str(path),'bytes':n,'rows':len(selected),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(root/'reports/benchmark-fixtures.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
