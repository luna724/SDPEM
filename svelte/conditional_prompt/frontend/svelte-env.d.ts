/// <reference types="svelte" />
/// <reference types="svelte2tsx/svelte-shims-v4" />
/// <reference types="svelte2tsx/svelte-jsx-v4" />

declare module "@gradio/dropdown" {
  import { SvelteComponentTyped } from "svelte";

  export default class Dropdown extends SvelteComponentTyped<Record<string, unknown>> {}
}
