<script lang="ts">
  import Message from "./Message.svelte";
  import ToolCallCard from "./ToolCallCard.svelte";

  function hasTextContent(content: any): boolean {
    if (!content) return false;
    if (typeof content === "string") return content.trim().length > 0;
    if (Array.isArray(content)) {
      return content.some((c: any) => c.text?.trim().length > 0);
    }
    return true;
  }

  let {
    messages = [],
    toolCalls = [],
    isLoading = false,
  }: {
    messages: any[];
    toolCalls: any[];
    isLoading?: boolean;
  } = $props();

  let containerEl: HTMLDivElement | undefined;

  $effect(() => {
    messages;
    if (containerEl) {
      requestAnimationFrame(() => {
        containerEl!.scrollTop = containerEl!.scrollHeight;
      });
    }
  });
</script>

<div
  bind:this={containerEl}
  class="flex-1 overflow-y-auto px-3 py-2 space-y-0 scroll-smooth"
>
  {#each messages as msg (msg.id)}
    {#if !(msg.type === "ai" && msg.tool_calls?.length > 0 && !hasTextContent(msg.content))}
      <Message {msg} />
    {/if}
    {#if msg.type === "ai" && msg.tool_calls?.length > 0}
      {#each msg.tool_calls as tc}
        {@const liveCall = toolCalls.find((t: any) => t.callId === tc.id) ?? tc}
        {#if liveCall}
          <ToolCallCard call={liveCall} />
        {/if}
      {/each}
    {/if}
  {/each}

  {#if isLoading}
    <div class="flex items-center gap-0.5 px-2 py-3 italic text-sm">
      {#each "Думаю...".split("") as char, i}
        <span
          class="inline-block shimmer-char text-slate-500"
          style="animation-delay: {i * 0.12}s"
        >{char}</span>
      {/each}
    </div>
  {/if}
</div>

<style>
  .shimmer-char {
    animation: shimmer 1.4s ease-in-out infinite;
  }
  @keyframes shimmer {
    0%, 100% { color: #64748b; }
    50% { color: #e2e8f0; }
  }
</style>
