<script>
  export let label = "サイズ";
  export let unit = "px";
  export let min = 0;
  export let max = 200;
  export let value = 80;
  export let step = 1;

  $: percentage = ((value - min) / (max - min)) * 100;
  function handleBlur() {
    if (value == null || isNaN(value)) {
      value = min; // 空っぽにされたら最小値に戻す
    } else {
      // 最小値と最大値の間に強制的に収める（Clamping）
      value = Math.max(min, Math.min(max, value));
    }
  }
</script>

<div class="slider-row">
  <div class="label-area">
    {label}
  </div>

  <div class="slider-wrapper">
    <input 
      type="range" 
      {min} {max} {step} 
      bind:value 
      class="custom-range"
      style="--progress: {percentage}%" 
    />
  </div>

  <div class="input-container">
    <input 
      type="number" 
      {min} {max} {step} 
      bind:value 
      on:blur={handleBlur} 
      on:keydown={(e) => e.key === 'Enter' && handleBlur()} 
      class="number-input-raw"
    />
    {#if unit}
      <span class="unit-suffix">{unit}</span>
    {/if}
  </div>
</div>

<style>
  /* 共通のレイアウトは前回と同じ */
  .slider-row {
    display: flex;
    align-items: center;
    gap: 0px 16px;
    padding: 0px 0;
    color: #ffffff;
    font-family: sans-serif;
  }
  .label-area { min-width: 60px; }
  .slider-wrapper { flex: 1; display: flex; align-items: center; }

  /* スライダーのバーとツマミのスタイル（前回と同じなので省略可） */
  .custom-range {
    -webkit-appearance: none; appearance: none; width: 100%; height: 6px;
    border-radius: 3px; outline: none;
    background: linear-gradient(to right, #a0c4ff var(--progress), #5a5e66 var(--progress));
  }
  .custom-range::-webkit-slider-thumb {
    -webkit-appearance: none; appearance: none; width: 8px; height: 24px;
    border-radius: 4px; background-color: #a0c4ff; border: 1px solid #1a1b1e; cursor: pointer;
  }
  .custom-range::-moz-range-thumb {
    width: 8px; height: 24px; border-radius: 4px; background-color: #a0c4ff;
    border: 1px solid #1a1b1e; cursor: pointer;
  }

  /* ====== 新しい入力ボックスのスタイル ====== */

  /* 1. 外側の枠線（ここが input タグに見えるようにする） */
  .input-container {
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 80px; /* 💡 65px -> 80px に広げて余裕を持たせる */
    border: 1px solid #4b5563;
    border-radius: 6px;
    padding: 4px 8px;
    background-color: transparent;
    transition: border-color 0.2s;
  }

  .number-input-raw {
    width: 45px; /* 💡 30px -> 45px に広げる（3〜4桁でも安心） */
    padding: 0;  /* 💡 ブラウザの隠れpaddingを消去して文字領域を最大化 */
    margin: 0;
    background: transparent;
    border: none;
    color: #ffffff;
    font-size: 0.9rem;
    text-align: right;
    outline: none;
  }

  /* 💡 超重要: 内部のinputがフォーカスされたら、親の枠線を光らせる */
  .input-container:focus-within {
    border-color: #a0c4ff;
  }

  /* 上下の矢印ボタンを消すおまじない */
  .number-input-raw::-webkit-inner-spin-button,
  .number-input-raw::-webkit-outer-spin-button {
    -webkit-appearance: none; margin: 0;
  }
  .number-input-raw { -moz-appearance: textfield; }

  /* 3. 単位のテキスト */
  .unit-suffix {
    color: #ffffff;
    font-size: 0.9rem;
    padding-left: 2px; /* 数字と少しだけ隙間をあける */
    pointer-events: none; /* クリックを邪魔しないようにする */
  }
</style>