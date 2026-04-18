<script>
  import {slide} from "svelte/transition";
  export let isOpen = false;
  export let title = "";

  function toggle() {
    isOpen = !isOpen;
  }
</script>

<div class="accordion">
  <button class="header" on:click={toggle}>
    <span class="title">{title}</span>
    <span class="chevron" class:open={isOpen}>◀</span>
  </button>

  {#if isOpen}
    <div class="content-wrapper" transition:slide={{ duration: 300 }}>
      <div class="content">
        <slot />
      </div>
    </div>
  {/if}
</div>

<style>
  /* 枠組みのデザイン */
  .accordion {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    margin-bottom: 8px;
    overflow: hidden; /* 角丸からはみ出ないようにする */
  }

  /* ボタンのデザイン */
  .header {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    background-color: #f9fafb;
    border: none;
    cursor: pointer;
    text-align: left;
    transition: background-color 0.2s;
  }

  .header:hover {
    background-color: #f3f4f6;
  }

  .title {
    font-weight: bold;
    color: #374151;
  }

  /* 矢印のデザインとアニメーション */
  .chevron {
    font-size: 0.8rem;
    color: #9ca3af;
    transition: transform 0.3s ease; /* 回転を滑らかにする */
  }

  /* isOpen が true になった時、矢印を180度回転させる */
  .chevron.open {
    transform: rotate(270deg);
  }

  /* 中身のデザイン */
  .content {
    padding: 16px;
    background-color: #ffffff;
    border-top: 1px solid #e5e7eb;
  }
</style>