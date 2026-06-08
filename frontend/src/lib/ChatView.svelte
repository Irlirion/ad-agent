<script lang="ts">
  import { useStream } from "@langchain/svelte";
  import MessageList from "./MessageList.svelte";
  import InputBar from "./InputBar.svelte";
  import WelcomeScreen from "./WelcomeScreen.svelte";

  let { onNewChat }: { onNewChat?: () => void } = $props();

  const stream = useStream({
    assistantId: "agent",
    apiUrl: import.meta.env.VITE_API_URL || "http://localhost/api",
  });

  let displayMessages = $state<any[]>([]);

  $effect(() => {
    displayMessages = stream.messages;
  });

  function send(text: string) {
    stream.submit({ messages: [{ type: "human", content: text }] });
  }
</script>

<div class="flex flex-col flex-1 min-h-0">
  {#if displayMessages.length === 0}
    <WelcomeScreen onSend={send} isLoading={stream.isLoading} />
  {:else}
    <div class="sticky top-0 z-10 flex items-center gap-3 bg-slate-900/90 backdrop-blur border-b border-slate-800 px-4 py-2">
      <button
        class="text-xs px-2 py-1 rounded border border-slate-700 text-slate-400 cursor-pointer hover:bg-slate-800 transition-colors"
        onclick={onNewChat}
      >
        + Новый диалог
      </button>
    </div>
    <MessageList
      messages={displayMessages}
      toolCalls={stream.toolCalls}
      isLoading={stream.isLoading}
    />
    <InputBar onSend={send} isLoading={stream.isLoading} />
  {/if}
</div>
