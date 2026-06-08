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

<div class="flex-1 flex flex-col items-center justify-center gap-5 px-4">
  <div class="text-slate-400">
    <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M6.5 6.5A7.5 7.5 0 0 0 14 17.5" />
      <path d="M14 17.5A7.5 7.5 0 0 0 17.5 14" />
      <path d="M10 10a4 4 0 0 0 5 5" />
      <circle cx="14" cy="14" r="5" />
      <path d="m17 7 3-3" />
      <path d="M20 4h-4v4" />
    </svg>
  </div>

  <h2 class="text-2xl font-semibold text-slate-200 text-center">
    Чем я могу вам помочь?
  </h2>

  <div class="flex gap-2 flex-wrap justify-center">
    {#each SUGGESTIONS as s}
      <button
        class="text-xs px-3 py-1.5 rounded-full border border-slate-700 text-slate-400 cursor-pointer hover:bg-slate-800 hover:text-slate-300 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        onclick={() => pickSuggestion(s)}
        disabled={isLoading}
      >
        {s}
      </button>
    {/each}
  </div>

  <div class="w-full max-w-xl flex gap-2 items-end">
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
