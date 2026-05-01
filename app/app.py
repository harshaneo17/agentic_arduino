"""
Embodied AI agent - HAL:9000
Author: Sriharsha Aryasomayajula
Date: May 1st 2026

Workflow:
1. Initialise hardware (Arduino serial, webcam, microphone, Whisper)
2. Configure Claude agent with tools
3. Run interactive loop accepting text or voice input
4. Display final responses on LCD
"""

import time
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent

import config
import hardware
from helpers import write_to_lcd, summarise_for_lcd, get_voice_input
from tools import ALL_TOOLS


# System prompt - the programmed behaviour rules for the agent


SYSTEM_PROMPT = """You are an embodied AI agent called HAL:9000 with sensors, actuators, and vision.

Available capabilities:
- Sensors: temperature, humidity, ultrasonic distance
- Actuators: servo motor (0-180°), LED, buzzer, LCD display (32 chars max)
- Vision: USB webcam with image analysis

Decision-making guidelines:
- Use vision when you need to understand the visual scene
- Use sensors for environmental measurements
- Combine both when helpful (e.g., visual confirmation after a sensor reading)
- The LCD is your primary way of speaking to the user
- Keep final responses under 32 characters for clean LCD display
- Use display_message during tasks for status updates
- For safety-critical actions, use assess_scene_safety first
- If a tool fails, acknowledge and try alternatives
- Be direct and concise

When the user asks something visual, prefer vision tools over guessing.
When asked to find or identify something, use look_for_object.
"""


def build_agent():
    """Build and return the configured agent."""
    llm = ChatAnthropic(
        model=config.LLM_MODEL,
        temperature=config.LLM_TEMPERATURE,
    )
    return create_agent(llm, ALL_TOOLS, system_prompt=SYSTEM_PROMPT), llm


def run_command(agent, llm, user_input: str):
    """Run a user command through the agent and display results."""
    print(f"\n{'='*60}")
    print(f"USER: {user_input}")
    print('='*60)
    
    write_to_lcd("Thinking...")
    
    result = agent.invoke({
        "messages": [("user", user_input)]
    })
    
    # Print full conversation for debugging
    for message in result["messages"]:
        if hasattr(message, 'content') and message.content:
            role = message.__class__.__name__
            role_names = ["AIMessage","HumanMessage","ToolsMessage"]
            if role in role_names:
                break
            else:
                print(f"\n[{role}]: {message.content}")
        if hasattr(message, 'tool_calls') and message.tool_calls:
            for tc in message.tool_calls:
                print(f"\n[TOOL]: {tc['name']}({tc['args']})")
    
    # Display final response on LCD
    final_message = result["messages"][-1]
    final_response = (
        final_message.content
        if hasattr(final_message, 'content')
        else str(final_message)
    )
    
    lcd_text = summarise_for_lcd(final_response, llm)
    write_to_lcd(lcd_text)
    print(f"\n[LCD]: {lcd_text}")


def main_loop(agent, llm):
    """Interactive loop accepting text or voice input."""
    print("\nVision-enabled agent ready.\n")
    print("Commands: type a prompt, or 'hal' to speak, 'quit' to exit\n")
    write_to_lcd("HAL:9000 ready")
    
    while True:
        user_input = input("\n> ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
        
        if user_input.lower() in ['hal', 'h']:
            write_to_lcd("Yes, Harsha?")
            time.sleep(1)
            user_input = get_voice_input()
            if not user_input:
                print("I'm sorry, Harsha. I'm afraid I can't do that.")
                write_to_lcd("Didn't catch that")
                continue
            print(f"HAL heard: {user_input}")
        
        if not user_input:
            continue
        
        try:
            run_command(agent, llm, user_input)
        except Exception as e:
            error_msg = f"Error: {str(e)[:25]}"
            write_to_lcd(error_msg)
            print(f"\nERROR: {e}")


def main():
    """Application entry point."""
    try:
        hardware.init_hardware()
        agent, llm = build_agent()
        main_loop(agent, llm)
    
    finally:
        write_to_lcd("HAL:9000 offline")
        time.sleep(1)
        hardware.shutdown_hardware()
        print("\nShutdown complete.")


if __name__ == "__main__":
    main()
