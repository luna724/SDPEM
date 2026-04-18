<script>
  export let label = "値の調整";
  export let min = 0;
  export let max = 100;
  export let step = 1;
  export let value = 50;
  export let unit = ""; 
</script>

<div class="slider-container">
  <div class="header">
    <span class="label">{label}</span>
    
    <span class="value-badge">{value}{unit}</span>
  </div>

  <input 
    type="range" 
    {min} 
    {max} 
    {step} 
    bind:value={value} 
    class="custom-slider"
  />
</div>

<style>
  .slider-container {
    display: flex;
    flex-direction: column;
    padding: 5px 10px;
    background-color: transparent;
    border-radius: 4px;
    border: 1px solid #ffffff1a;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .label {
    color: #ffffff;
    padding-bottom: 2px;
  }

  .value-badge {
    background-color: #719fe91f; /* 青色のバッジ */
    color: white;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.8rem;
  }

  /* スライダーのスタイル */
  .custom-slider {
    width: 99%;
    cursor: pointer;
    
    /* 💡 プロのテクニック：これ1行でスライダーの色をモダンに変えられます！ */
    accent-color: #205fc5d3; 
  }
</style>