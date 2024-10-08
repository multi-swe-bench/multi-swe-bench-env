<h1 align="center">
  <img src="assets/figures/logo.png" width="7%" alt="multi-swe-bench logo" style="vertical-align:middle;">
  Multi-SWE-bench Evaluation
</h1>

<p align="center">
  <a href="https://huggingface.co/datasets/Daoguang/Multi-SWE-bench">📁 Dataset</a> &nbsp;|&nbsp;
  <a href="https://multi-swe-bench.github.io">🏆 Leaderboard</a> &nbsp;|&nbsp;
  <a href="https://arxiv.org/abs/2408.14354">📄 Paper</a> &nbsp;|&nbsp;
  <a href="https://discord.gg/HEU3gvyXUf">💬 Discord</a>
</p>


## 📰 News
* **[Aug. 27, 2024]**:We’ve released the JAVA version of [SWE-bench](https://www.swebench.com)! Check it out on [Hugging Face](https://huggingface.co/datasets/Daoguang/Multi-SWE-bench). For more details, see our [paper](https://arxiv.org/pdf/2408.14354)!

## 🔧 Modifications

This repository is a modified version of [SWE-bench](https://github.com/princeton-nlp/SWE-bench). If needed, please refer to their [evaluation process](https://github.com/princeton-nlp/SWE-bench) for guidance.

## 🚀 Set Up
1. Docker setup
Multi-SWE-bench uses Docker for reproducible evaluations.
Follow the instructions in the [Docker setup guide](https://docs.docker.com/engine/install/) to install Docker on your machine.
If you're setting up on Linux, we recommend seeing the [post-installation steps](https://docs.docker.com/engine/install/linux-postinstall/) as well.

2. Build Multi-SWE-bench
To build Multi-SWE-bench from source, follow these steps:
```bash
git clone git@github.com:multi-swe-bench/multi-swe-bench-env.git
cd multi-swe-bench-env
pip install -e .
```
3. Install repositories
Install repositories locally to avoid repeatedly downloading repositories when running evaluations:
```bash
mkdir repos
cd repos
git clone https://github.com/google/gson.git
git clone https://github.com/FasterXML/jackson-databind.git
git clone https://github.com/FasterXML/jackson-core.git
git clone https://github.com/FasterXML/jackson-dataformat-xml.git
git clone https://github.com/apache/dubbo.git
git clone https://github.com/GoogleContainerTools/jib.git
```

4. Validate installation
Test your installation by running:
```bash
cd ..
python -m swebench.harness.run_evaluation \
    --predictions_path gold \
    --max_workers 1 \
    --instance_ids apache__dubbo-10638 \
    --run_id validate-gold
```


## 📊 Evaluation
Use `swebench.harness.run_evaluation` to evaluate your predictions on Multi-SWE-bench:
```bash
python -m swebench.harness.run_evaluation \
    --dataset_name Daoguang/Multi-SWE-bench \
    --predictions_path <path_to_predictions> \
    --max_workers <num_workers> \
    --run_id <run_id>
    # use --predictions_path 'gold' to verify the gold patches
    # use --run_id to name the evaluation run
```

You can also evaluate on specific issue instances:
```bash
python -m swebench.harness.run_evaluation \
    --dataset_name Daoguang/Multi-SWE-bench \
    --predictions_path <path_to_predictions> \
    --max_workers <num_workers> \
    --run_id <run_id> \
    --instance_ids <instance_id>
```

The outputs include:
- docker build logs under the `build_image_logs` directory
- evaluation logs under the `run_instance_logs` directory
- a result summary in the `<prediction_file_name>.<run_id>.json` file

## 📄 Citation

If you found [SWE-bench](https://arxiv.org/abs/2310.06770) or [Multi-SWE-bench]() helpful for your work, please cite as follows:

```
@inproceedings{jimenez2024swebench,
    title={{SWE}-bench: Can Language Models Resolve Real-world Github Issues?},
    author={Carlos E Jimenez and John Yang and Alexander Wettig and Shunyu Yao and Kexin Pei and Ofir Press and Karthik R Narasimhan},
    booktitle={The Twelfth International Conference on Learning Representations},
    year={2024},
    url={https://openreview.net/forum?id=VTF8yNQM66}
}
```

```
@misc{zan2024swebenchjava,
  title={SWE-bench-java: A GitHub Issue Resolving Benchmark for Java}, 
  author={Daoguang Zan and Zhirong Huang and Ailun Yu and Shaoxin Lin and Yifan Shi and Wei Liu and Dong Chen and Zongshuai Qi and Hao Yu and Lei Yu and Dezhi Ran and Muhan Zeng and Bo Shen and Pan Bian and Guangtai Liang and Bei Guan and Pengjie Huang and Tao Xie and Yongji Wang and Qianxiang Wang},
  year={2024},
  eprint={2408.14354},
  archivePrefix={arXiv},
  primaryClass={cs.SE},
  url={https://arxiv.org/abs/2408.14354}, 
}
```

## 🙏 Acknowledgements

We express our deepest gratitude to the authors of the [SWE-bench](https://github.com/princeton-nlp/SWE-bench) dataset, whose foundational work our project is built upon.

## 🪪 License
MIT. Check [LICENSE.md](./LICENSE).
