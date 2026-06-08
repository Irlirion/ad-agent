<script lang="ts">
  import ChatView from "./lib/ChatView.svelte";

  let sessionKey = $state(0);

  function newChat() {
    sessionKey++;
  }
</script>

<div class="flex h-screen w-screen overflow-hidden bg-slate-900 text-slate-200">
  <main class="flex-1 flex flex-col min-w-0">
    {#key sessionKey}
      <ChatView onNewChat={newChat} />
    {/key}
  </main>
</div>
