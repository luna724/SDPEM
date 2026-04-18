<script lang="ts">
  /// <reference path="./svelte-env.d.ts" />

  import PercentageCard from './Percentage.svelte';
  import Dropdown from "@gradio/dropdown";

  type ConditionType = "percentage" | "if_has";

  type Condition = {
    type: ConditionType;
    key: string;
    add: string;
    and_condition: unknown[];
    or_condition: unknown[];
  };
  
  type PercentageCondition = Condition & {
    type: "percentage";
    percent: number;
  };

  type AnyCondition = PercentageCondition;

  type GradioLike = {
    dispatch: (event: string) => void;
    autoscroll?: boolean;
    i18n?: unknown;
  };

  export let value: AnyCondition[] | null = [];
  export let label = "";
  export let elem_id = "";
  export let elem_classes: string[] = [];
  export let interactive = true;
  export let gradio: GradioLike;

  let last_cond_id = 0;
  const availableConditions: [string, ConditionType][] = [
    ["percentage", "percentage"],
    ["if_has", "if_has"]
  ];
  let toAddCondition: ConditionType = "percentage";
  let safe_value: AnyCondition[] = value || [];
  let typed_value: AnyCondition[] = safe_value;

  let mockGradio: GradioLike;
  $: mockGradio = {
    ...gradio,
    dispatch: (event: string) => {
      if (["change"].includes(event)) return
      console.log(`Event dispatched: ${event}`);
    }
  };

  $: safe_value = value || [];
  $: typed_value = safe_value;

  function addPercentageCondition(): void {
    safe_value = [...safe_value, {
      type: "percentage",
      key: `percentage-${last_cond_id}`,
      percent: 100,
      add: "",
      and_condition: [],
      or_condition: []
    }];
    value = safe_value;

    gradio.dispatch("change");
  }

  function removeCondition(index: number): void {
    safe_value.splice(index, 1);
    safe_value = safe_value;
    value = safe_value;
    gradio.dispatch("change");
  }

  function addCondition(): void {
    last_cond_id += 1;
    if (toAddCondition === "percentage") {
      addPercentageCondition();
    }
  }

  function isCondition(cond: unknown, type: ConditionType): cond is Condition {
    return (
      typeof cond === "object" &&
      cond !== null &&
      "type" in cond &&
      (cond as { type?: unknown }).type === type
    );
  }
</script>

<div id={elem_id} class="builder-container {elem_classes.join(' ')}">
  
  {#if label}
    <div class="component-label">{label}</div>
  {/if}

  {#each typed_value as cond, i}
    {@const otherConditions = safe_value.filter((v, idx) => idx !== i && v.key !== "").map(v => v.key)}
    {@const oc = otherConditions.map(k => [k, k])}

    {#if isCondition(cond, "percentage")}
      <PercentageCard 
        bind:cond={cond} 
        otherConditions={oc} 
        gradio={mockGradio}
        onDelete={() => removeCondition(i)} 
      />
    {/if}
  {/each}

  <!--追加処理-->
  {#if interactive}
  <div class="row">
    <Dropdown
      gradio={mockGradio}
      bind:value={toAddCondition}
      choices={availableConditions}
      label="condition type"
      max_choices=1
      container=false
      interactive={interactive}
    />

    <button class="add-btn" on:click={addCondition}>+ Add Condition</button>
  </div>
  {/if}
</div>

<style> 
  .row { display: flex; gap: 10px; flex: 1; border: 1px solid #fff; justify-content: center; }
  .row > :global(*) { flex: 1; flex-grow: 1; }
  .builder-container { display: flex; flex-direction: column; gap: 1rem; }
  .component-label { font-weight: bold; margin-bottom: 0.5rem; color: #374151; }
  .add-btn { padding: 0px; background-color: #c4832e; color: rgb(0, 0, 0); border-radius: 11px; cursor: pointer; font-size: medium;}
</style>