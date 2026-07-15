<script setup lang="ts">
import { computed, ref } from "vue";

const props = withDefaults(
  defineProps<{
    title: string;
    url: string;
    summary: string;
    maintainer?: string;
    repoUrl?: string;
    status?: string;
    tags?: string;
    copyLabel?: string;
    copiedLabel?: string;
    openLabel?: string;
    repoLabel?: string;
  }>(),
  {
    maintainer: "",
    repoUrl: "",
    status: "",
    tags: "",
    copyLabel: "Copy Link",
    copiedLabel: "Copied",
    openLabel: "Open",
    repoLabel: "GitHub Repo"
  }
);

const copied = ref(false);

const tagList = computed(() =>
  props.tags
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean)
);

async function copyUrl() {
  try {
    await navigator.clipboard.writeText(props.url);
    copied.value = true;
    window.setTimeout(() => {
      copied.value = false;
    }, 1600);
  } catch {
    copied.value = false;
  }
}
</script>

<template>
  <article class="store-source-card">
    <div class="store-source-card__head">
      <div>
        <h3>{{ title }}</h3>
        <p>{{ summary }}</p>
      </div>
      <span v-if="status" class="store-source-card__status">{{ status }}</span>
    </div>

    <div class="store-source-card__meta">
      <span v-if="maintainer">Maintainer: {{ maintainer }}</span>
      <div v-if="tagList.length" class="store-source-card__tags">
        <span v-for="tag in tagList" :key="tag" class="store-source-card__tag">{{ tag }}</span>
      </div>
    </div>

    <div class="store-source-card__url">
      <code>{{ url }}</code>
    </div>

    <div class="store-source-card__actions">
      <button type="button" class="store-source-card__button store-source-card__button--brand" @click="copyUrl">
        {{ copied ? copiedLabel : copyLabel }}
      </button>
      <a class="store-source-card__button store-source-card__button--ghost" :href="url" target="_blank" rel="noreferrer">
        {{ openLabel }}
      </a>
      <a
        v-if="repoUrl"
        class="store-source-card__button store-source-card__button--ghost"
        :href="repoUrl"
        target="_blank"
        rel="noreferrer"
      >
        <svg
          class="store-source-card__button-icon"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            fill="currentColor"
            d="M12 .5C5.65.5.5 5.66.5 12.02c0 5.09 3.29 9.41 7.86 10.93.58.11.79-.25.79-.56 0-.27-.01-1.17-.02-2.12-3.2.7-3.88-1.36-3.88-1.36-.52-1.34-1.28-1.69-1.28-1.69-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.2 1.77 1.2 1.03 1.77 2.69 1.26 3.34.97.1-.75.4-1.26.73-1.55-2.55-.29-5.23-1.28-5.23-5.67 0-1.25.45-2.27 1.19-3.08-.12-.29-.52-1.46.11-3.04 0 0 .97-.31 3.19 1.18a10.9 10.9 0 0 1 5.82 0c2.21-1.49 3.18-1.18 3.18-1.18.64 1.58.24 2.75.12 3.04.74.81 1.18 1.83 1.18 3.08 0 4.4-2.68 5.37-5.24 5.66.41.35.77 1.04.77 2.1 0 1.52-.01 2.74-.01 3.12 0 .31.21.68.8.56a11.53 11.53 0 0 0 7.85-10.93C23.5 5.66 18.35.5 12 .5Z"
          />
        </svg>
        {{ repoLabel }}
      </a>
    </div>
  </article>
</template>
