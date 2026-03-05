<script>
  import { createEventDispatcher } from 'svelte';
  import { classifyAudio, fetchSampleFile } from '../lib/api.js';
  import ResultsDisplay from './ResultsDisplay.svelte';

  const dispatch = createEventDispatcher();

  let audioFile = null;
  let audioUrl = null;
  let labelsText = '';
  let results = [];
  let loading = false;
  let error = null;

  // Sample audio clips
  const sampleAudios = [
    { name: 'Dog Barking', file: 'audio/dog_bark.wav' },
    { name: 'Traffic', file: 'audio/traffic.wav' },
    { name: 'Music', file: 'audio/music.wav' },
    { name: 'Speech', file: 'audio/speech.wav' },
  ];

  // Pre-built label sets
  const labelPresets = {
    small: ['dog barking', 'cat meowing', 'bird chirping', 'car horn', 'music', 'speech', 'rain', 'thunder', 'wind', 'silence'],
    sounds: [
      'dog barking', 'cat meowing', 'bird chirping', 'rooster crowing', 'cow mooing',
      'horse neighing', 'sheep bleating', 'pig oinking', 'lion roaring', 'wolf howling',
      'car horn', 'car engine', 'motorcycle', 'truck', 'airplane', 'helicopter', 'train',
      'siren', 'alarm', 'doorbell', 'phone ringing', 'keyboard typing', 'mouse clicking',
      'rain', 'thunder', 'wind', 'water flowing', 'ocean waves', 'fire crackling',
      'footsteps', 'door closing', 'glass breaking', 'explosion', 'gunshot'
    ],
    music: [
      'piano', 'guitar', 'violin', 'drums', 'bass', 'flute', 'trumpet', 'saxophone',
      'singing', 'humming', 'whistling', 'clapping', 'classical music', 'jazz', 'rock',
      'pop music', 'electronic music', 'hip hop', 'country music', 'orchestra'
    ],
    speech: [
      'male speech', 'female speech', 'child speaking', 'whispering', 'shouting',
      'laughing', 'crying', 'coughing', 'sneezing', 'breathing', 'snoring',
      'conversation', 'crowd talking', 'applause', 'cheering', 'booing'
    ],
    medium: Array.from({ length: 100 }, (_, i) => `sound_${i + 1}`),
    large: Array.from({ length: 500 }, (_, i) => `audio_${i + 1}`),
  };

  function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
      audioFile = file;
      audioUrl = URL.createObjectURL(file);
      error = null;
    }
  }

  async function loadSample(sample) {
    try {
      loading = true;
      error = null;
      audioFile = await fetchSampleFile(sample.file);
      audioUrl = URL.createObjectURL(audioFile);
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
    if (!audioFile) {
      error = 'Please select or upload an audio file first';
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
      const response = await classifyAudio(audioFile, labels);
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

<div class="clap-demo">
  <div class="input-section">
    <div class="audio-input">
      <h3>Audio Input</h3>

      <div class="samples">
        <span class="label">Samples:</span>
        {#each sampleAudios as sample}
          <button class="sample-btn" on:click={() => loadSample(sample)}>
            {sample.name}
          </button>
        {/each}
      </div>

      {#if audioUrl}
        <div class="audio-loaded">
          <div class="audio-preview">
            <div class="waveform-icon">
              <svg viewBox="0 0 100 40" fill="none">
                <rect x="5" y="10" width="4" height="20" rx="2" fill="currentColor" />
                <rect x="15" y="5" width="4" height="30" rx="2" fill="currentColor" />
                <rect x="25" y="12" width="4" height="16" rx="2" fill="currentColor" />
                <rect x="35" y="2" width="4" height="36" rx="2" fill="currentColor" />
                <rect x="45" y="8" width="4" height="24" rx="2" fill="currentColor" />
                <rect x="55" y="14" width="4" height="12" rx="2" fill="currentColor" />
                <rect x="65" y="6" width="4" height="28" rx="2" fill="currentColor" />
                <rect x="75" y="10" width="4" height="20" rx="2" fill="currentColor" />
                <rect x="85" y="15" width="4" height="10" rx="2" fill="currentColor" />
              </svg>
            </div>
            <audio controls src={audioUrl}></audio>
            <div class="file-info">
              <span class="filename">{audioFile?.name}</span>
              <label class="change-file-btn">
                Change
                <input
                  type="file"
                  accept="audio/*"
                  on:change={handleFileSelect}
                  class="hidden-input"
                />
              </label>
            </div>
          </div>
        </div>
      {:else}
        <div class="upload-area">
          <div class="placeholder">
            <span>Drop an audio file or click to upload</span>
          </div>
          <input
            type="file"
            accept="audio/*"
            on:change={handleFileSelect}
            class="file-input"
          />
        </div>
      {/if}
    </div>

    <div class="labels-input">
      <h3>Candidate Labels</h3>

      <div class="presets">
        <span class="label">Presets:</span>
        <button on:click={() => loadPreset('small')}>10 Basic</button>
        <button on:click={() => loadPreset('sounds')}>35 Sounds</button>
        <button on:click={() => loadPreset('music')}>20 Music</button>
        <button on:click={() => loadPreset('speech')}>16 Speech</button>
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
    {loading ? 'Classifying...' : 'Classify Audio'}
  </button>

  {#if error}
    <div class="error">{error}</div>
  {/if}

  <ResultsDisplay {results} {loading} />
</div>

<style>
  .clap-demo {
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
    min-height: 150px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: border-color 0.2s;
  }

  .upload-area:hover {
    border-color: #a78bfa;
  }

  .audio-loaded {
    border: 2px solid #334155;
    border-radius: 8px;
    overflow: hidden;
    min-height: 150px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #0f172a;
  }

  .audio-preview {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    width: 100%;
  }

  .waveform-icon {
    color: #a78bfa;
    width: 100px;
  }

  .audio-preview audio {
    width: 100%;
    max-width: 300px;
  }

  .file-info {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    width: 100%;
    justify-content: center;
  }

  .filename {
    font-size: 0.75rem;
    color: #64748b;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 200px;
  }

  .change-file-btn {
    font-size: 0.75rem;
    color: #a78bfa;
    cursor: pointer;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    transition: background 0.2s;
  }

  .change-file-btn:hover {
    background: rgba(167, 139, 250, 0.1);
  }

  .hidden-input {
    display: none;
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
    border-color: #a78bfa;
  }

  .label-count {
    margin-top: 0.5rem;
    font-size: 0.75rem;
    color: #64748b;
    text-align: right;
  }

  .classify-btn {
    padding: 1rem 2rem;
    background: linear-gradient(135deg, #8b5cf6, #a78bfa);
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
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
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
