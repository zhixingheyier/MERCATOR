# **MERCATOR**: Threat-hunting-oriented attack graph construction using fine-tuned large language model

## 1. Architecture
<!-- ![image-20240202161151479](./images/total_pipeline.jpg)
<img src="./images/total_pipeline.jpg" width="800" height="200"> -->
<div align="center">
  <img src="./0_images/total_pipeline.jpg" width="800" height="400">
</div>


## 2. Example
<!-- ![image-20240202161151479](./images/Example.jpg) -->
<div align="center">
  <img src="./0_images/Example.jpg" width="700" height="500">
</div>

## 3. Code Structure

### 1_raw cti reports
- reports sources
  - This folder contains the source urls of reports collected from various sources (e.g., Microsoft, Talos, etc.). Each subfolder contains the urls of a specific source.
  - All of these urls are used to collect CTI reports, which are the raw data for *AAGC*.
  - We use *Selenium* and *PrintFriendly* tools to collect the reports from these urls, and the collected reports are in the form of HTML or PDF.

- preprocess
  - HTML_format
    - We use the *BeautifulSoup* tool to extract the text from HTML files. All of the extracted data are stored in the same folder.
  - PDF_format
    - We use the *MinerU* tool to extract the text from PDF files, and each subfolder contains a PDF file and its extracted text as example.
  - All of the extracted data are stored in the JOSN format.

### 2_block division
- D-SC dataset construction and data refinement
  - `preprocess_data_from_pdf.ipynb` --> This notebook is used to preprocess the data from PDF files. It not only extracts the labeled data (if the section's headings belong to tactics) to construct fine-turn dataset *D-SC*, but also reorganizes the raw files into a more structured format (section-wise) for further processing.
  - `preprocess_data_from_html.ipynb` --> This notebook is used to preprocess the data from HTML files, as `preprocess_data_from_pdf.ipynb` did.
  - Folder `heading_related_tactical_stage` and `reorganized_reports` --> These folders contain the preprocessed data from both PDF and HTML files. Each subfolder contains the preprocessed data from a specific source. We just retain some of the preprocessed data for convenience.
  - `construct_D_SC.ipynb` --> This notebook is used to construct the fine-tuned dataset *D-SC* from `heading_related_tactical_stage`. We split the training and testing subsets at a ratio of 8:2.
  - `refine_reports.ipynb` --> This notebook is used to refine the preprocessed data from `reorganized_reports`. We filtered some low quality reports.
  - `refined_reports` --> This folder contains the refined data.

### 3_finetuned LLMs
- *M_classifier*
  - fine-tune_dataset_for_stage_identification --> This folder contains the fine-tuned dataset *D-SC* for *M_classifier*.
  - Fine-tuned *M_classifier*
    - We leverage the open-source fine-tuning framework `Llama-Factory` to fine-tune *M_classifier* on the fine-tuned dataset *D-SC_train*. The config file `data_info.json` and fine-tuned model's weight are saved in the `fine-tuned_M_classifier` folder.
    - For more details about `Llama-Factory`, please refer to the [Llama-Factory official documentation](https://github.com/hiyouga/LLaMAFactory).
  
- *M_extractor*
  - fine-tune_dataset_for_element_extraction --> This folder contains the fine-tuned dataset *D-EE* for *M_extractor*.
  - Fine-tuned *M_extractor*
    - As the same as *M_classifier*, we leverage `Llama-Factory` to fine-tune *M_extractor* on the fine-tuned dataset *D-EE*. Note that we fine-tuned two version LLMs (with-CoT and without-CoT) for *M_extractor*.

- *M_mapper*
  - fine-tune_dataset_for_semantic_alignment --> This folder contains the fine-tuned dataset *D-SA* for *M_mapper*.
  - Fine-tuned *M_mapper*
    - We fine-tune *M_mapper* on *D-SA*. Note that we also fine-tuned two version LLMs (with-CoT and without-CoT) for *M_mapper*.

### 4_workflow
- Inference --> This folder contains the inference scripts for using fine-tuned *M_classifier*, *M_extractor* and *M_mapper*. All of the inference scripts are used in Llama-Factory.
  - Usage example (Note: should change the paths according to your own environment in the scripts):
    ```
    API_PORT=8000 llamafactory-cli api inference_llama3-1-8B-sft.yaml
    ```
- AG_construction --> We construct attack graphs in the *D_PE* dataset.
    - Code --> This folder contains the scripts for constructing the attack graphs from CTI reports based on the fine-tuned LLMs.
    - x_Data_xx --> These folders contain the datas generated in various steps during the construction of attack graph.


## 4. Notes
- The python version is `Python 3.10.9`.
- The conda environment file is `mywork_1_env.yaml`.


