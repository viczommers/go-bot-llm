# Protocol Wrapper for LLMs to play Go (Weiqi/Baduk) ○●  
[GTP (Go Text Protocol)](https://senseis.xmp.net/?GoTextProtocol) engine implementation to connect LLMs to [Sabaki GUI](https://github.com/SabakiHQ/Sabaki)
## Supports
- Azure OpenAI GPT-4o (2024-12-01-preview)
- Azure grok-4-fast-reasoning (2025-01-01-preview)

##  HOWTO
- `MAX_RETRIES_PER_GAME` var controls total number of illegal moves allowed (up to 3 attempts per game, then automatic resignation)

## Setup for Sabaki GUI (Mac)
1. Go Sabaki > Settings.. > Engines Tab > Add
2. In `Path` field, specify path to your Python env (e.g. `/Users/victor/Desktop/Git-Repos/wally/.venv/bin/python`)
3. In `Arguments` field, specify path to your .py file (e.g. `/Users/victor/Desktop/Git-Repos/wally/wally_llm.py`)

## Config Setup
create `config.py`, it should contain:
### Azure
- `API_KEY` = "xyz"
- `AZURE_ENDPOINT` = "xyz.openai.azure.com/"

### API versions for different models
- `AZURE_API_VERSION` = "2024-12-01-preview"
- `GROK_API_VERSION` = "2025-01-01-preview" 

### Model deployments
- `AZURE_DEPLOYMENT` = "gpt-4o"
- `GROK_DEPLOYMENT` = "grok-4-fast-reasoning"

## Wally (Mechanical AI)
Reconstruction of the Wally - simple GO program written by Jonathan K. Millen for KIM-1<br>
Wally is a GTP engine that needs GUI to tun under,<br>
tested with fantastic cross-platform Sabaki GUI:<br>
https://github.com/SabakiHQ/Sabaki

- Original article https://archive.org/details/byte-magazine-1981-04/page/n101/mode/2up
- Original Repo https://github.com/maksimKorzh/wally
