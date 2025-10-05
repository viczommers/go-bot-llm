from models import GoMoveResponse
from config import API_KEY, AZURE_API_VERSION, AZURE_ENDPOINT, DEEPSEEK_DEPLOYMENT
from openai import AzureOpenAI
import json
import sys
import re

def eprint(*args, **kwargs):
    """Print to stderr for logging"""
    print(*args, file=sys.stderr, **kwargs)

client = AzureOpenAI(
    api_key=API_KEY,
    api_version=AZURE_API_VERSION,
    azure_endpoint=AZURE_ENDPOINT
)

system_prompt = """You are an expert Go player with deep knowledge of strategy, tactics, and joseki (opening patterns).

Analyze positions carefully considering:
- Group safety and liberty count
- Territory and influence balance
- Strategic direction of play
- Tactical move sequences
- Formation quality and efficiency

IMPORTANT: Go coordinates use letters A-H, J-T (the letter 'I' is skipped to avoid confusion with 1).
Valid coordinates: A1-T19 (excluding I). Examples: D4, K10, Q16 are valid. I4, I10 are INVALID.
"""

def format_board_as_text(board, board_width, board_range):
    """Convert board array to readable text format for LLM"""
    lines = []

    # Add column headers
    if board_width == 9:
        lines.append("    A B C D E F G H J")
    elif board_width == 13:
        lines.append("    A B C D E F G H J K L M N")
    else:  # 19x19
        lines.append("    A B C D E F G H J K L M N O P Q R S T")

    # Add rows
    for row in range(1, board_range - 1):
        line = f"{board_width - row + 1:2d}  " if board_width - row + 1 >= 10 else f" {board_width - row + 1}  "
        for col in range(1, board_range - 1):
            idx = row * board_range + col
            piece = board[idx]
            # 0 = empty, 1 = black, 2 = white, 7 = offboard
            if piece == 0:
                line += ". "
            elif piece & 1:  # Black stone
                line += "X "
            elif piece & 2:  # White stone
                line += "O "
        lines.append(line.rstrip())

    return "\n".join(lines)

def get_deepseek_move(board, board_width, board_range, move_history, color):
    """
    Query DeepSeek R1 for Go move suggestion

    Note: DeepSeek may not support strict json_schema through Azure AI.
    This function tries structured output first, falls back to JSON mode if needed.

    Args:
        board: List representing the board state
        board_width: Size of the board (9, 13, or 19)
        board_range: board_width + 2 (includes margins)
        move_history: List of previous moves
        color: 1 for Black, 2 for White

    Returns:
        dict with keys: move_type, move, reasoning, thinking, tokens
        or None if request fails
    """
    try:
        # Format board for LLM
        board_str = format_board_as_text(board, board_width, board_range)

        # Format move history
        if move_history:
            moves_str = "\n".join([f"{i+1}. {move}" for i, move in enumerate(move_history)])
        else:
            moves_str = "No moves yet (start of game)"

        color_name = 'Black (X)' if color == 1 else 'White (O)'

        user_prompt = f"""You are playing Go on a {board_width}x{board_width} board.

Current Board State:
{board_str}

Move History:
{moves_str}

You are playing as {color_name}.

Rules reminder:
- Empty intersections are marked with '.'
- Black stones are marked with 'X'
- White stones are marked with 'O'
- Coordinates use A-H, J-T (letter 'I' is NOT used). Examples: D4, K10, Q16
- You can play 'PASS' if no good move is available

Analyze the position and suggest your next move. Consider:
1. Taking opponent stones with only 1 liberty remaining
2. Defending your own groups with limited liberties
3. Building territory and influence
4. Creating strong formations

Think through the position step by step:
- What are the key areas on the board?
- What are the tactical opportunities?
- What move sequences did you consider?
- Why is your chosen move optimal?

IMPORTANT: Respond with valid JSON in this exact format:
{{
  "move_type": "coordinate",
  "move": "D4",
  "reasoning": "Brief explanation here",
  "thinking": "Detailed thought process here"
}}

move_type must be: 'coordinate', 'pass', or 'resign'
move must be: valid coordinate like 'D4', or 'PASS', or 'RESIGN'"""

        eprint(f"Querying DeepSeek R1 ({DEEPSEEK_DEPLOYMENT}) for move suggestion...")

        # DeepSeek R1 on Azure only supports basic JSON mode
        response = client.chat.completions.create(
            model=DEEPSEEK_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt + "\n\nIMPORTANT: You MUST respond with ONLY valid JSON. No markdown, no code blocks, no explanations - just raw JSON."},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content.strip()

        # Remove markdown code blocks and preamble text if present
        if "```json" in content:
            content = content.split("```json")[-1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[-2].strip()

        # Extract JSON object if there's preamble text
        if content.startswith("{"):
            # Already clean JSON
            pass
        else:
            # Find the first { and extract from there
            json_start = content.find("{")
            if json_start != -1:
                content = content[json_start:]

        # Parse JSON manually
        move_data = json.loads(content)
        move_type = move_data.get('move_type', 'coordinate')
        move = move_data.get('move', '').strip().upper()
        reasoning = move_data.get('reasoning', '')
        thinking = move_data.get('thinking', '')
        tokens = vars(response.usage) if hasattr(response, 'usage') else {}

        eprint("DeepSeek R1 using JSON mode")

        # Log the response
        eprint(f"\nDeepSeek R1 suggested move: {move} (type: {move_type})")
        if thinking:
            eprint(f"\n=== THINKING PROCESS ===")
            eprint(thinking)
            eprint("========================\n")
        eprint(f"Reasoning: {reasoning}\n")

        return {
            'move_type': move_type,
            'move': move,
            'reasoning': reasoning,
            'thinking': thinking,
            'tokens': tokens
        }

    except Exception as e:
        # Content filter errors are common with Go terminology - just retry
        if "ContentFilterFinishReasonError" in str(type(e).__name__):
            eprint(f"Content filter triggered (common with Go terms) - will retry")
        else:
            eprint(f"ERROR: Failed to call DeepSeek R1: {e}")
        return None
