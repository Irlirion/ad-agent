<script lang="ts">
  let { call }: { call: any } = $props();

  const isRunning = $derived(call.status === "running");
  const isFinished = $derived(call.status === "finished");
  const isError = $derived(call.status === "error");
  const isVisualize = $derived(call.name === "visualize");
  const isImage = $derived(isVisualize && typeof call.output === "string" && call.output.length > 100);
  const autoOpen = $derived(isImage || isError);

  let resultOpen = $state(false);
  let elapsed = $state(0);

  $effect(() => {
    if (autoOpen) resultOpen = true;
  });

  $effect(() => {
    if (isRunning) {
      elapsed = 0;
      const timer = setInterval(() => elapsed++, 1000);
      return () => clearInterval(timer);
    }
  });

  const borderColor = $derived(
    isError ? "border-red-500/50"
    : isRunning ? "border-purple-500/50"
    : "border-green-500/50"
  );
</script>

{#if isVisualize && isFinished && isImage}
  <!-- Visualize tool: always show image, auto-expanded -->
  <div class="border rounded-lg {borderColor} bg-slate-950 p-2 mb-2">
    <div class="flex items-center gap-2 mb-1">
      <span class="text-green-400 text-sm">✓</span>
      <span class="text-sky-400 font-mono font-semibold text-xs">{call.name}</span>
      <span class="text-slate-500 text-[10px]">(готово)</span>
    </div>
    <img src="data:image/png;base64,{call.output}" alt="visualization" class="max-w-full rounded max-h-96 object-contain" />
  </div>
{:else}
  <div class="border rounded-lg {borderColor} bg-slate-950 p-2 mb-2 text-xs">
    <div class="flex items-center gap-2">
      {#if isRunning}
        <div class="w-3.5 h-3.5 border-2 border-purple-400/30 border-t-purple-400 rounded-full animate-spin shrink-0"></div>
      {:else}
        <span class="text-sm {isError ? 'text-red-400' : 'text-green-400'}">
          {isError ? "✕" : "✓"}
        </span>
      {/if}
      <span class="text-sky-400 font-mono font-semibold">{call.name}</span>
      {#if isRunning}
        <span class="text-purple-400 text-[10px]">({elapsed}s)</span>
      {:else}
        <span class="text-slate-500 text-[10px]">
          {isError ? "(ошибка)" : "(готово)"}
        </span>
      {/if}
      {#if isFinished && !autoOpen}
        <button
          class="ml-auto text-[10px] px-1.5 py-0.5 rounded border border-slate-700 text-slate-400 cursor-pointer hover:bg-slate-800"
          onclick={() => resultOpen = !resultOpen}
        >
          {resultOpen ? "скрыть" : "показать"}
        </button>
      {/if}
    </div>

    {#if isError && call.error && !resultOpen}
      <div class="text-red-400 mt-1 text-[11px]">{call.error}</div>
    {/if}

    {#if resultOpen}
      <div class="mt-2 space-y-2">
        <div>
          <div class="text-[10px] text-slate-500 uppercase tracking-wider mb-0.5">вход</div>
          <pre class="m-0 p-1.5 bg-slate-900 rounded overflow-x-auto text-slate-400 text-[11px] max-h-[150px] overflow-y-auto">{JSON.stringify(call.args ?? call.input, null, 2)}</pre>
        </div>
        {#if isFinished && call.output != null}
          <div>
            <div class="text-[10px] text-slate-500 uppercase tracking-wider mb-0.5">выход</div>
            <pre class="m-0 p-1.5 bg-slate-900 rounded overflow-x-auto text-slate-400 text-[11px] max-h-[150px] overflow-y-auto">{JSON.stringify(call.output, null, 2)}</pre>
          </div>
        {/if}
        {#if isError && call.error}
          <div>
            <div class="text-[10px] text-slate-500 uppercase tracking-wider mb-0.5">ошибка</div>
            <pre class="m-0 p-1.5 bg-slate-900 rounded text-red-400 text-[11px]">{call.error}</pre>
          </div>
        {/if}
      </div>
    {/if}
  </div>
{/if}
