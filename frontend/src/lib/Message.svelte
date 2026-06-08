<script lang="ts">
  import { marked } from "marked";
  import DOMPurify from "dompurify";
  import katex from "katex";
  import "katex/dist/katex.min.css";

  marked.use({
    extensions: [
      {
        name: "inlineMath",
        level: "inline",
        start(src: string) { return src.indexOf("$"); },
        tokenizer(this: any, src: string) {
          const match = src.match(/^\$([^$\n]+?)\$/);
          if (match) return { type: "inlineMath", raw: match[0], text: match[1].trim() };
        },
        renderer(token: any) {
          return katex.renderToString(token.text, { throwOnError: false });
        },
      },
      {
        name: "blockMath",
        level: "block",
        start(src: string) { return src.indexOf("$$"); },
        tokenizer(this: any, src: string) {
          const match = src.match(/^\$\$([\s\S]+?)\$\$/);
          if (match) return { type: "blockMath", raw: match[0], text: match[1].trim() };
        },
        renderer(token: any) {
          return katex.renderToString(token.text, { throwOnError: false, displayMode: true });
        },
      },
    ],
  });

  let { msg }: { msg: any } = $props();

  const isTool = $derived(msg.type === "tool");
  const isHuman = $derived(msg.type === "human");
  const contentText = $derived(
    typeof msg.content === "string"
      ? msg.content
      : Array.isArray(msg.content)
        ? msg.content.map((c: any) => c.text ?? "").join("")
        : ""
  );
  const htmlContent = $derived(
    isHuman
      ? contentText
      : DOMPurify.sanitize(marked.parse(contentText, { async: false }))
  );
  const isBase64Image = $derived(
    !isHuman &&
    typeof msg.content === "string" &&
    msg.content.length > 100 &&
    /^[A-Za-z0-9+/=]+$/.test(msg.content.slice(0, 100))
  );
  const time = $derived(
    msg.created_at
      ? new Date(msg.created_at).toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })
      : ""
  );

  let lightboxOpen = $state(false);
</script>

{#if !isTool}
<div class="flex {isHuman ? 'justify-end' : 'justify-start'} mb-2">
  <div class="flex gap-2 max-w-[80%] {isHuman ? 'flex-row-reverse' : 'flex-row'}">
    <!-- Avatar -->
    <div
      class="w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs font-bold mt-1 {isHuman
        ? 'bg-blue-600 text-white'
        : 'bg-slate-700 text-sky-400'}"
      title={isHuman ? "Вы" : "Агент"}
    >
      {isHuman ? "В" : "А"}
    </div>

    <!-- Bubble -->
    <div
      class="rounded-lg px-3 py-2 {isHuman
        ? 'bg-blue-900/60 rounded-tr-sm'
        : 'bg-slate-800 rounded-tl-sm'} {isBase64Image ? 'p-1' : ''}"
      title={time || undefined}
    >
      {#if isBase64Image}
        <button
          class="block cursor-pointer"
          onclick={() => lightboxOpen = true}
          onkeydown={(e) => e.key === 'Enter' && (lightboxOpen = true)}
        >
          <img
            src="data:image/png;base64,{msg.content}"
            alt="visualization"
            class="max-w-full rounded max-h-96 object-contain"
          />
        </button>
      {:else}
        <div class="prose-custom text-sm leading-relaxed">
          {@html htmlContent}
        </div>
      {/if}
    </div>
  </div>
</div>
{/if}

<!-- Lightbox -->
{#if lightboxOpen}
  <div
    role="button"
    tabindex="0"
    class="fixed inset-0 z-50 bg-black/80 flex items-center justify-center cursor-pointer"
    onclick={() => lightboxOpen = false}
    onkeydown={(e) => (e.key === 'Enter' || e.key === 'Escape') && (lightboxOpen = false)}
  >
    <button
      class="bg-transparent p-0 border-0 cursor-default"
      onclick={(e) => e.stopPropagation()}
    >
      <img
        src="data:image/png;base64,{msg.content}"
        alt="visualization"
        class="max-w-[90vw] max-h-[90vh] object-contain rounded"
      />
    </button>
  </div>
{/if}

<style>
  :global(.prose-custom p) { margin: 0 0 0.4rem; }
  :global(.prose-custom p:last-child) { margin-bottom: 0; }
  :global(.prose-custom ul), :global(.prose-custom ol) { margin: 0.3rem 0; padding-left: 1.2rem; }
  :global(.prose-custom li) { margin-bottom: 0.15rem; }
  :global(.prose-custom code) {
    background: #020617;
    padding: 0.1rem 0.3rem;
    border-radius: 4px;
    font-size: 0.85em;
  }
  :global(.prose-custom pre) {
    background: #020617;
    padding: 0.6rem;
    border-radius: 6px;
    overflow-x: auto;
    margin: 0.4rem 0;
  }
  :global(.prose-custom pre code) { padding: 0; background: none; }
  :global(.prose-custom h1), :global(.prose-custom h2), :global(.prose-custom h3) {
    margin: 0.6rem 0 0.3rem;
    color: #e2e8f0;
  }
  :global(.prose-custom a) { color: #38bdf8; }
  :global(.prose-custom table) {
    border-collapse: collapse;
    margin: 0.4rem 0;
    font-size: 0.85rem;
    width: 100%;
  }
  :global(.prose-custom th), :global(.prose-custom td) {
    border: 1px solid #334155;
    padding: 0.3rem 0.5rem;
    text-align: left;
  }
  :global(.prose-custom th) { background: #1e293b; }
  :global(.prose-custom blockquote) {
    border-left: 3px solid #334155;
    margin: 0.4rem 0;
    padding: 0.2rem 0.6rem;
    color: #94a3b8;
  }
  :global(.prose-custom hr) {
    border: none;
    border-top: 1px solid #334155;
    margin: 0.6rem 0;
  }
</style>
