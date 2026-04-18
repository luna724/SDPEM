<script>
  import Card from "./common/Card.svelte";
  import Slider from "./common/Slider.svelte";

  // 親(Index.svelte)から受け取るデータ
  export let cond;       // このカード自身のデータ (key, percent, addなど)
  export let otherConditions;  // 自分以外の条件のKeyリスト (ドロップダウン用)
  export let onDelete;   // 削除ボタンが押された時の関数
  export let gradio;
</script>

<Card
  bind:cond={cond}
  theme="percentage"
  onDelete={onDelete}
  otherConditions={otherConditions}
  gradio={gradio}
>
  <div class="break"></div>
  <div class="input-group highlight-field">
    <Slider
      label="threshold",
      min=0.1 max=99.9 step=0.1
      bind:value={cond.percent}
      unit="%"
    />
  </div>
</Card>

<style>
.break {
  flex-basis: 100%;
  height: 0;
}

.input-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex: 1;
    min-width: 120px;
  }

</style>