# Protocol Wrapper for LLMs to play Go (Weiqi/Baduk) ○●  
[GTP (Go Text Protocol)](https://senseis.xmp.net/?GoTextProtocol) engine implementation to connect LLMs to [Sabaki GUI](https://github.com/SabakiHQ/Sabaki).
## Download Slides [HERE (reveal.js html)](https://github.com/viczommers/go-bot-llm/blob/main/slides/slides.html)

## Supports
- Azure OpenAI GPT-4o (2024-12-01-preview)
- Azure OpenAI o4-mini (2025-04-01-preview)
- Azure grok-4-fast-reasoning (2025-01-01-preview)
- Azure DeepSeek-R1-0528 (2024-12-01-preview)

## Tournament Logs
- Contains Logs with LLM reasoning and moves
- Contains .SGF files (moves/board positions)

## Usage Metrics
| Model | Total Tokens | Cost per 1M Tokens | Total Moves | Cost per Move |
|-------|--------------|--------------------|-------------|---------------|
| O4-mini | 3.59M | $4.40/M | ~305 | ~5.1¢/Move |
| DeepSeek-R1 | 3.37M | $5.40/M | ~365 | ~4.9¢/Move |
| Grok-4-fast | 944.95K | $1.73/M | ~388 | ~0.4¢/Move |
| GPT-4o | 1.91M | $10.00/M | ~924 | ~2.0¢/Move |

*Total moves are approx (+/- 10%); Token costs per Azure AI Foundry;

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
- `AZURE_ENDPOINT` = "https://xyz.openai.azure.com/"

### API versions for different models
- `AZURE_API_VERSION` = "2024-12-01-preview"
- `GROK_API_VERSION` = "2025-01-01-preview" 

### Model deployments
- `AZURE_DEPLOYMENT` = "gpt-4o" or "o4-mini"
- `GROK_DEPLOYMENT` = "grok-4-fast-reasoning"
- `DEEPSEEK_DEPLOYMENT` = "DeepSeek-R1-0528"

## Katago:
- Origina Repo https://github.com/lightvector/KataGo/

## Wally (Mechanical AI)
Reconstruction of the Wally - simple GO program written by Jonathan K. Millen for KIM-1<br>
Wally is a GTP engine that needs GUI to turn under
- Original article https://archive.org/details/byte-magazine-1981-04/page/n101/mode/2up
- Original Repo https://github.com/maksimKorzh/wally
