<script>
  import { slide } from "svelte/transition";
  import Dropdown from "@gradio/dropdown";
  
  export let onDelete; //: callable

  export let theme; //: string
  export let cond; //: Condition
  export let gradio; //: mockGradio
  export let otherConditions; //: string[]

  export let isOpen = true;
</script>

<div class="condition-card {theme}">
  <button class="card-header" on:click={() => isOpen = !isOpen}>
    <div class="gradio-row center-col">
      <div class="title-circle"></div>
      <div class="title-badge">{theme} ({cond.key})</div>
    </div>
    <span class="chevron" class:open={isOpen}>▼</span>
  </button>

  {#if isOpen}
    <div class="content-wrapper" transition:slide={{ duration: 300 }}>
      <div class="content">
        <div class="card-body">
          <div class="input-group">
            <span>Key</span>
            <input type="text" placeholder="condition ID" bind:value={cond.key} />
          </div>
          
          <div class="input-group">
            <span>Prompt to add</span>
            <input type="text" placeholder="" bind:value={cond.add} />
          </div>
          
          <slot />

        </div>

        <div class="card-footer">
          <div class="gradio-row">
            <Dropdown 
              gradio={gradio}
              bind:value={cond.and_condition}
              choices={otherConditions} placeholder="AND..."
              label="AND condition"
              class="item"
              interactive=true
              multiselect=true
            />
            
            <Dropdown 
              gradio={gradio}
              bind:value={cond.or_condition} 
              choices={otherConditions} placeholder="OR..."
              label="OR condition" 
              class="item"
              interactive=true
              multiselect=true
            />
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .percentage {
    --color: 34, 64, 146;
  }
  .flex-2 { flex: 2; }

  .gradio-row {
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap; 
    gap: var(--size-4); 
    width: 100%;
  }

  .item {
    flex: 1 1 0%; 
    min-width: 200px;
    display: flex; 
    flex-direction: column;
  }

  .center-col {
    align-items: center;
  }

  .condition-card {
    border: 1px solid #ffffff71;
    border-radius: 8px;
    background-color: transparent; /* 親の背景色に馴染む */
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background-color: rgba(var(--color), 0.5);
    border-bottom: 1px solid #e5e7eb;
  }
  .title-circle {
    width: 15px;  /* 丸のサイズはお好みで調整 */
    height: 15px;
    border-radius: 50%; /* 完全な丸にする */
    background-color: rgba(var(--color), 1);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
  }
  .title-badge {
    font-weight: bold;
    color: #ffffff;
    font-size: 0.9rem;
    letter-spacing: 0.03em;
  }
  .delete-btn {
    background: none; border: none; color: #ef4444;
    cursor: pointer; font-size: 0.85rem; font-weight: bold;
  }
  .delete-btn:hover { text-decoration: underline; }

  .card-body {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    padding: 12px;
  }
  .input-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex: 1;
    min-width: 120px;
  }
  .input-group input {
    padding: 6px; border: 1px solid #d1d5db6b; border-radius: 4px; font-size: 0.9rem;
    background-color: transparent;
  }
  .input-group input::placeholder { color: #6d6d6d; }

  .card-footer {
    display: flex;
    gap: 12px;
    padding: 12px;
    border-top: 1px dashed #d1d5db;
    background-color: rgba(0,0,0, 0.02);
  }
  .select-group { flex: 1; display: flex; flex-direction: column; gap: 4px; }

  .highlight-field input { border-color: #3b82f6; background-color: #eff6ff; }

  .chevron {
    font-size: 0.8rem;
    color: #9ca3af;
    transition: transform 0.3s ease; /* 回転を滑らかにする */
  }

  .chevron.open {
    transform: rotate(-90deg);
  }

</style>
