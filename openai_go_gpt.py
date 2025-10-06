from models import GoMoveResponse
from config import API_KEY, AZURE_API_VERSION, AZURE_ENDPOINT, AZURE_DEPLOYMENT_2
from openai import AzureOpenAI
import json
import sys
import traceback
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

def get_go_move(board, board_width, board_range, move_history, color):
    """
    Query Azure OpenAI for Go move suggestion using structured output

    Args:
        board: List representing the board state
        board_width: Size of the board (9, 13, or 19)
        board_range: board_width + 2 (includes margins)
        move_history: List of previous moves
        color: 1 for Black, 2 for White

    Returns:
        dict with keys: move, reasoning, thinking, tokens
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

Provide your response with:
- move_type: 'coordinate' for normal moves, 'pass' for passing, 'resign' if position is hopeless
- move: The actual coordinate (e.g., 'D4', 'K10') or 'PASS' or 'RESIGN'
- reasoning: Brief explanation of your choice
- thinking: Your detailed thought process"""

        # Check if this is a reasoning model (o1, o1-preview, o1-mini)
        is_reasoning_model = any(x in AZURE_DEPLOYMENT_2.lower() for x in ['o1', 'reasoning'])

        eprint("Querying Azure OpenAI for move suggestion...")

        if is_reasoning_model:
            # For reasoning models, use standard completion (they don't support structured output yet)
            eprint("Using reasoning model - accessing internal thoughts...")
            response = client.chat.completions.create(
                model=AZURE_DEPLOYMENT_2,
                messages=[
                    {"role": "user", "content": user_prompt + "\n\nProvide your response in JSON format with fields: move, reasoning, thinking"}
                ],
                temperature=1.0,  # Reasoning models use fixed temperature
                max_completion_tokens=5000
            )

            # Try to parse JSON response
            content = response.choices[0].message.content

            # Print reasoning tokens if available (for o1 models)
            if hasattr(response.choices[0].message, 'reasoning_content') and response.choices[0].message.reasoning_content:
                eprint("\n=== MODEL THINKING PROCESS ===")
                eprint(response.choices[0].message.reasoning_content)
                eprint("==============================\n")

            try:
                move_data = json.loads(content)
                move_type = move_data.get('move_type', 'coordinate')
                move = move_data.get('move', '').strip().upper()
                reasoning = move_data.get('reasoning', '')
                thinking = move_data.get('thinking', '')
            except:
                # Fallback: try to extract move from text
                eprint(f"Could not parse JSON, raw response: {content}")
                match = re.search(r'[A-T]\d{1,2}|PASS', content, re.IGNORECASE)
                if match:
                    move = match.group(0).upper()
                    reasoning = content
                    thinking = ""
                else:
                    eprint("ERROR: Could not extract move from response")
                    return None

            tokens = vars(response.usage) if hasattr(response, 'usage') else {}

        else:
            # For standard models, use structured output
            response = client.beta.chat.completions.parse(
                model=AZURE_DEPLOYMENT_2,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=GoMoveResponse,
                # temperature=0.7,
                # max_tokens=1000
            )

            # Extract structured response
            move_response = response.choices[0].message.parsed
            move_type = move_response.move_type
            move = move_response.move.strip().upper()
            reasoning = move_response.reasoning
            thinking = move_response.thinking if move_response.thinking else ""
            tokens = vars(response.usage) if hasattr(response, 'usage') else {}

        # Log the response
        eprint(f"\nLLM suggested move: {move} (type: {move_type})")
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
            eprint(f"ERROR: Failed to call Azure OpenAI: {e}")
            # eprint(traceback.format_exc())
        return None
