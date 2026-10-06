# Input-Output Analysis for Hawaii

This repository contains examples and a program to run a Leontief Input-Output model (as well as some other things in a future date) using the IO tables
prepared by the Department of Business, Economic Development, and Tourism (DBEDT) from the State of Hawaii. 

DBEDT publishes their IO tables every five years or so, with the latest release being in 2022, and their last in 2017. The department covers the methodology and provides the files, which are used in this repository as well. 

Anyone also familiar with these models know that the Burea of Economic Analysis (BEA) also publishes national-level tables that are also quite useful. This repository does not focus on that. 


## TODO
1. I need to do a front-end? Maybe something simple like streamlit
2. Needs to do both the intercounty and condensed and uncondensed state... though given that it's all automated we can just do uncondensed. 


## Structure

```
.
├── data
│   ├── 2022-inter-county.xlsx
│   ├── 2022-State-IO-Condensed_Final.xlsx
│   └── 2022-State-IO-Detailed_Final.xlsx
├── README.md
├── src
│   └── main.py
```

<h2>Frequently Asked Questions</h2>

<details>
  <summary><b>1. Are input output models good?</b></summary>
  <br>
  <p>"Good" is very broad, but IO models have been in service for quite a long time and have been used extensively in the policy world. From my point of view, they can be sufficient for small things, but IO models should have their primary usage for "back-of-the-envelope" simulations that need to be done quickly with results that are relatively easy to understand.</p>
  <p>There are iterations on the idea that are significantly more robust to criticism, like computable general equilibrium (CGE) models. I will be working on a separate repository for that.</p>
  <p>I like to describe IO models with this analogy. <b>When you are hungry and you have nothing else to eat, then go to the vending machine. => If you are in dire need of economic modeling and you don't have viable alternatives, go to an IO model.</b></p>
</details>


<details>
  <summary><b>2. What other IO Modeling options are there?</b></summary>
  <br>
  <p>The most common model (and the inspiration for this project) is the IMPLAN input-output model which is developed and sold privately. It has become one of the most common tools used in policy analysis, which spurred my interest in making a free and open-source (FOSS) alternative for Hawaii's policy specifically. UHERO has sporadically used IO models when they deem appropriate, such as when they looked at the <a href="https://governor.hawaii.gov/newsroom/news-release-total-economic-impact-generated-by-nelha-host-park-jumps-significantly-to-more-than-145-million-annually/">economic impact of a park in 2024</a>.</p> 
</details>