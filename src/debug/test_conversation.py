import sys
import os

# Ensure both the src and modules directories are in the path for import
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
modules_dir = os.path.join(base_dir, 'modules')
src_dir = base_dir
sys.path.insert(0, modules_dir)
sys.path.insert(0, src_dir)

from conversation import LlmModule


def test_conversation_basic():
    """
    Basic test for LlmModule: instantiates and runs a simple exchange.
    """
    conv = LlmModule(debug=True)
    # Example: simulate a conversation turn
    try:
        messages = [
            {"role": "system", "content": "You are Robbie the Robot, a robot who is being built by Heidi and Heidi's daddy. Your responses should be mostly short, kind, off-kilter, and suitable for a 6 year old. No sound effects."},
            {"role": "user", "content": "Hello, robot!"}
        ]
        response = conv.chat_llm(messages)
        print(f"Robot response: {response}")
    except Exception as e:
        print(f"Error during conversation test: {e}")


if __name__ == "__main__":
    print("[Conversation Debug] Starting basic test...")
    test_conversation_basic()
    print("[Conversation Debug] Test complete.")
