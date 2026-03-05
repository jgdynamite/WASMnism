<script>
  import { createEventDispatcher } from 'svelte';
  import { classifyImage, fetchSampleFile } from '../lib/api.js';
  import ResultsDisplay from './ResultsDisplay.svelte';

  const dispatch = createEventDispatcher();

  let imageFile = null;
  let imagePreview = null;
  let labelsText = '';
  let results = [];
  let loading = false;
  let error = null;

  // Sample images
  const sampleImages = [
    { name: 'Cat', file: 'images/cat.jpg' },
    { name: 'City Street', file: 'images/street.jpg' },
    { name: 'Food', file: 'images/food.jpg' },
    { name: 'Mountain', file: 'images/mountain.jpg' },
  ];

  // Pre-built label sets
  const labelPresets = {
    small: ['cat', 'dog', 'bird', 'fish', 'horse', 'elephant', 'tiger', 'lion', 'bear', 'monkey'],
    animals: [
      'cat', 'dog', 'bird', 'fish', 'horse', 'cow', 'sheep', 'pig', 'chicken', 'duck',
      'elephant', 'tiger', 'lion', 'bear', 'monkey', 'gorilla', 'zebra', 'giraffe', 'deer', 'rabbit',
      'squirrel', 'fox', 'wolf', 'owl', 'eagle', 'penguin', 'dolphin', 'whale', 'shark', 'turtle',
      'snake', 'frog', 'butterfly', 'bee', 'ant', 'spider', 'crab', 'lobster', 'octopus', 'jellyfish'
    ],
    scenes: [
      'beach', 'mountain', 'forest', 'desert', 'city street', 'countryside', 'river', 'lake',
      'ocean', 'sunset', 'sunrise', 'night sky', 'cloudy sky', 'rainy day', 'snowy landscape',
      'park', 'garden', 'farm', 'highway', 'bridge', 'building', 'skyscraper', 'house', 'castle'
    ],
    food: [
      'pizza', 'burger', 'sushi', 'pasta', 'salad', 'steak', 'chicken', 'fish', 'rice', 'bread',
      'cake', 'ice cream', 'fruit', 'vegetables', 'soup', 'sandwich', 'taco', 'noodles', 'curry', 'breakfast'
    ],
    medium: Array.from({ length: 100 }, (_, i) => `object_${i + 1}`),
    large: Array.from({ length: 500 }, (_, i) => `category_${i + 1}`),
  };

  function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
      imageFile = file;
      imagePreview = URL.createObjectURL(file);
      error = null;
    }
  }

  async function loadSample(sample) {
    try {
      loading = true;
      error = null;
      imageFile = await fetchSampleFile(sample.file);
      imagePreview = URL.createObjectURL(imageFile);
    } catch (e) {
      error = `Failed to load sample: ${e.message}`;
    } finally {
      loading = false;
    }
  }

  function loadPreset(presetName) {
    labelsText = labelPresets[presetName].join('\n');
  }

  async function classify() {
    if (!imageFile) {
      error = 'Please select or upload an image first';
      return;
    }

    const labels = labelsText
      .split(/[,\n]/)
      .map(l => l.trim())
      .filter(l => l.length > 0);

    if (labels.length === 0) {
      error = 'Please enter at least one label';
      return;
    }

    try {
      loading = true;
      error = null;
      const response = await classifyImage(imageFile, labels);
      results = response.results;
      dispatch('result', response);
    } catch (e) {
      error = e.message;
      results = [];
    } finally {
      loading = false;
    }
  }
</script>

<div class="clip-demo">
  <div class="input-section">
    <div class="image-input">
      <h3>Image Input</h3>

      <div class="samples">
        <span class="label">Samples:</span>
        {#each sampleImages as sample}
          <button class="sample-btn" on:click={() => loadSample(sample)}>
            {sample.name}
          </button>
        {/each}
      </div>

      <div class="upload-area">
        {#if imagePreview}
          <img src={imagePreview} alt="Preview" class="preview" />
        {:else}
          <div class="placeholder">
            <span>Drop an image or click to upload</span>
          </div>
        {/if}
        <input
          type="file"
          accept="image/*"
          on:change={handleFileSelect}
          class="file-input"
        />
      </div>
    </div>

    <div class="labels-input">
      <h3>Candidate Labels</h3>

      <div class="presets">
        <span class="label">Presets:</span>
        <button on:click={() => loadPreset('small')}>10 Animals</button>
        <button on:click={() => loadPreset('animals')}>40 Animals</button>
        <button on:click={() => loadPreset('scenes')}>24 Scenes</button>
        <button on:click={() => loadPreset('food')}>20 Foods</button>
        <button on:click={() => loadPreset('medium')}>100 Generic</button>
        <button on:click={() => loadPreset('large')}>500 Generic</button>
      </div>

      <textarea
        bind:value={labelsText}
        placeholder="Enter labels (one per line or comma-separated)"
        rows="8"
      ></textarea>

      <div class="label-count">
        {labelsText.split(/[,\n]/).filter(l => l.trim()).length} labels
      </div>
    </div>
  </div>

  <button class="classify-btn" on:click={classify} disabled={loading}>
    {loading ? 'Classifying...' : 'Classify Image'}
  </button>

  {#if error}
    <div class="error">{error}</div>
  {/if}

  <ResultsDisplay {results} {loading} />
</div>

<style>
  .clip-demo {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .input-section {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }

  @media (max-width: 768px) {
    .input-section {
      grid-template-columns: 1fr;
    }
  }

  h3 {
    margin: 0 0 0.75rem;
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94a3b8;
  }

  .samples, .presets {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
    align-items: center;
  }

  .samples .label, .presets .label {
    font-size: 0.75rem;
    color: #64748b;
  }

  .sample-btn, .presets button {
    padding: 0.375rem 0.75rem;
    background: #334155;
    border: none;
    border-radius: 6px;
    color: #e2e8f0;
    font-size: 0.75rem;
    cursor: pointer;
    transition: background 0.2s;
  }

  .sample-btn:hover, .presets button:hover {
    background: #475569;
  }

  .upload-area {
    position: relative;
    border: 2px dashed #334155;
    border-radius: 8px;
    overflow: hidden;
    aspect-ratio: 4/3;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: border-color 0.2s;
  }

  .upload-area:hover {
    border-color: #60a5fa;
  }

  .preview {
    width: 100%;
    height: 100%;
    object-fit: contain;
    background: #0f172a;
  }

  .placeholder {
    color: #64748b;
    text-align: center;
    padding: 2rem;
  }

  .file-input {
    position: absolute;
    inset: 0;
    opacity: 0;
    cursor: pointer;
  }

  textarea {
    width: 100%;
    padding: 0.75rem;
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 8px;
    color: #e2e8f0;
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 0.875rem;
    resize: vertical;
  }

  textarea:focus {
    outline: none;
    border-color: #60a5fa;
  }

  .label-count {
    margin-top: 0.5rem;
    font-size: 0.75rem;
    color: #64748b;
    text-align: right;
  }

  .classify-btn {
    padding: 1rem 2rem;
    background: linear-gradient(135deg, #3b82f6, #60a5fa);
    border: none;
    border-radius: 8px;
    color: white;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
  }

  .classify-btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
  }

  .classify-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .error {
    padding: 0.75rem;
    background: #7f1d1d;
    border-radius: 8px;
    color: #fecaca;
    font-size: 0.875rem;
  }
</style>
