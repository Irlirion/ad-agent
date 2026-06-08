<script lang="ts">
  import { SUGGESTIONS } from "./suggestions";

  let { onSend, isLoading = false }: { onSend: (text: string) => void; isLoading?: boolean } = $props();

  let input = $state("");
  let isFocused = $state(false);
  let textareaEl: HTMLTextAreaElement | undefined;

  function send() {
    if (!input.trim() || isLoading) return;
    onSend(input.trim());
    input = "";
    resetHeight();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  function resetHeight() {
    if (textareaEl) {
      textareaEl.style.height = "auto";
    }
  }

  function autoResize() {
    if (textareaEl) {
      textareaEl.style.height = "auto";
      textareaEl.style.height = Math.min(textareaEl.scrollHeight, 6 * 24) + "px";
    }
  }

  function pickSuggestion(s: string) {
    onSend(s);
  }
</script>

<div class="border-t border-slate-800 bg-slate-900/80 pt-2 pb-3 px-2">
  <!-- Suggestion chips when input is empty and not focused -->
  {#if !input.trim() && !isFocused}
    <div class="flex gap-1.5 mb-2 px-1 flex-wrap">
      {#each SUGGESTIONS as s}
        <button
          class="text-[11px] px-2 py-1 rounded-full border border-slate-700 text-slate-400 cursor-pointer hover:bg-slate-800 hover:text-slate-300 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          onclick={() => pickSuggestion(s)}
          disabled={isLoading}
        >
          {s}
        </button>
      {/each}
    </div>
  {/if}

  <div class="flex gap-2 items-end">
    <textarea
      bind:this={textareaEl}
      bind:value={input}
      onkeydown={handleKeydown}
      onfocus={() => isFocused = true}
      onblur={() => isFocused = false}
      oninput={autoResize}
      placeholder="Исследовать данные телеметрии..."
      rows="1"
      class="flex-1 resize-none rounded-lg px-3 py-2 bg-slate-800 border border-slate-700 text-slate-200 text-sm placeholder:text-slate-500 outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-all"
    ></textarea>
    <button
      onclick={send}
      disabled={!isLoading && !input.trim()}
      class="h-10 px-4 rounded-lg font-semibold text-sm transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed {isLoading
        ? 'bg-red-600 hover:bg-red-700 text-white'
        : 'bg-blue-600 hover:bg-blue-700 text-white'}"
    >
      {isLoading ? "■" : "Отправить"}
    </button>
  </div>
</div>
