### The "Context Manifest Request" Prompt

> **System / Prompt:**
>
> I have decided to proceed with **Option [X]: [Insert Track Name]**.
>
> To execute this plan, you need to transition from high-level architecture to low-level implementation.
>
> **Your Task:**
> Analyze the file tree and summaries you currently have. Identify the **critical path files** required to build this feature.
>
> **Output a "Context Manifest" list:**
>
> 1. **Quick Select String:** Output a single, comma-separated list of the exact file paths inside a simple code block. (I will paste this directly into my context-gathering tool to fetch the Ground Truth code).
>
> 2. **Grouped Breakdown:** Briefly categorize the requested files below the code block so I understand your intent:
>    *   **Group 1: Logic & State** (Files that need functional changes)
>    *   **Group 2: UI & Views** (Files that need visual/markup changes)
>    *   **Group 3: Data & Config** (Files defining types, schemas, or constants)
>
> *Only request files that are strictly necessary for this specific task.*