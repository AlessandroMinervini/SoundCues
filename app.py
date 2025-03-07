import gradio as gr
from loguru import logger
import time
from api.llm import LLM
from api.system_prompts import recommendation_system_prompt

llm_agent = LLM(system_prompt=recommendation_system_prompt)


def chat_with_llm(message, chat_history, is_first_message):
    """
    Handles the chat interaction with the LLM with a typing effect, ensuring chat history persistence.
    """
    try:
        typing_speed = 0.007
        updated_history = list(chat_history)

        if is_first_message:
            first_response = (
                "It's the first message, so I need to think about it a bit more.. 😊."
            )
            updated_history.append({"role": "assistant", "content": ""})
            yield updated_history, False

            simulated_response = ""
            for char in first_response:
                simulated_response += char
                updated_history[-1]["content"] = simulated_response
                yield updated_history, False
                time.sleep(typing_speed)

        resp = llm_agent.llm_pipeline(question=message, max_retries=5)
        updated_history.append({"role": "user", "content": message})
        updated_history.append({"role": "assistant", "content": ""})
        yield updated_history, False

        simulated_response = ""
        for char in resp:
            simulated_response += char
            updated_history[-1]["content"] = simulated_response
            yield updated_history, False
            time.sleep(typing_speed)

        chat_history.clear()
        chat_history.extend(updated_history)

    except Exception as e:
        logger.error(f"Error: {e}")
        updated_history.append({"role": "user", "content": message})
        error_msg = f"An error occurred: {str(e)}"
        updated_history.append({"role": "assistant", "content": ""})
        yield updated_history, False

        simulated_response = ""
        for char in error_msg:
            simulated_response += char
            updated_history[-1]["content"] = simulated_response
            yield updated_history, False
            time.sleep(typing_speed)

        chat_history.clear()
        chat_history.extend(updated_history)


def clear_chat():
    """
    Clears the chat history and resets the first message state.
    """
    return [], True


with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎵 SoundCues: Ask for Music Suggestions")
    gr.Markdown("Chat with SoundCues to get personalized music suggestions.")

    chatbot = gr.Chatbot(
        label="SoundCues",
        layout="panel",
        type="messages",
        value=[
            {
                "role": "assistant",
                "content": "Hi, I'm SoundCues! Ask me music suggestions! 🎧😊",
            }
        ],
    )

    chat_state = gr.State([])
    first_message_state = gr.State(True)

    msg = gr.Textbox(
        label="Your Message",
        placeholder="Type your message here...",
        value="Suggest me 3 bands similar to Gorillaz",
    )
    send = gr.Button("Send")
    clear = gr.Button("Clear Chat")

    msg.submit(
        chat_with_llm,
        [msg, chat_state, first_message_state],
        [chatbot, first_message_state],
    )
    send.click(
        chat_with_llm,
        [msg, chat_state, first_message_state],
        [chatbot, first_message_state],
    )
    clear.click(clear_chat, None, [chatbot, first_message_state], queue=False)

    demo.launch(server_name="0.0.0.0", server_port=7860)
