# 🦙 Ollama Adaptive Image Code Gen 🧠

> <b> Fun Fact : -</b> LLMs can sometimes “hallucinate” information, which means they might generate details that sound plausible but are made up. It’s like when someone tells a creative but fictional story and you’re unsure if they’re joking or serious!

<hr/>

## Project WorkFlow and What it actually do :smirk:

1. <b>Please refer 'Control Flow Diagram' of Application before moving ahead :point_down:</b>

![OLLaMa Image Adaptive Code Gen WorkFlow](media/OLLaMa%20Image%20Adaptive%20Code%20Gen%20WorkFlow.png)


2. <b>What Does this application actually do:grey_question:</b>

    1. First, it initiates the **LLaMa 3.1 8B LLM Model** using `ollama`. You can also change the LLM model if you want to by editing the path `config/config.json` ([For Using Model within `Python Code`]) and `entrypoint.sh` ([For Pulling `ModelFiles`]).

    2. Then, the LLM model chooses: **`Dimension`**, **`Shape`**, **`Color`**, and **`Area`**. It then generates the `Python code` for drawing an `Image` with the same specifications. The generated code will be stored at the path: `oLLaMa_generated_code_dir/generated_code.py`.

    3. Then, it will **install all the dependencies** required before executing `generated_code.py`. After the successful installation of the necessary modules, it will execute `generated_code.py`.

    4. The **`Generated Code`** is also sent back to the `LLM Model` for verification to ensure all `Specifications` mentioned in the image are met. If the verification is successful, the execution will `stop` with `Exit Code: 0`. Otherwise, it will `Rectify the Generated Code` and repeat all the steps from `Step No. iii` mentioned above.

> Just a small catch :see_no_evil: : This application is totally **`Asynchronous`** in nature.


<hr/>

## Application Setup Guidelines :bookmark_tabs:

1. <b>Dependency Installations </b> 
    - Make an virtual enviorment and install all the necessary components to run the 'Application'

    ```
    virtualenv venv
    ```

    - Activate your virtual enviorment

    ```
    - For MacOS:
        source venv/bin/activate

    - For Windows:
        venv\Scripts\activate.bat
    ```

    - Install all the necessary ingredients from `requirements.txt` file:

    ```
    pip3 install -r requirements.txt
    ```

> To Learn More About `virtualenv`: [Click Here](https://docs.python.org/3/tutorial/venv.html)

2. <b>Project setup and Containarization</b>
    - Start <b>'Docker Desktop'</b> application and open terminal in your <b>'Working directory'</b> [Where `docker-compose.yaml` and `Dockerfile` is located]. Then run below given command to 'Build' an `oLLaMa Image`

    ```
    docker compose build
    ```

    - After completion of the <b>'Image Building'</b> process. It's time to `compose up` LLM in our Local System using:

    ```
    docker compose up
    ```

    - `NOTE:` Compose up process might upto <b>20 - 25 Mins.</b> first time. Because it will download all the respective `ModelFiles`.

> For Download guide of `Docker Desktop` For <b>MacOS</b>: [Click Here](https://docs.docker.com/desktop/install/mac-install/)

> For Download guide of `Docker Desktop` For <b>Windows</b>: [Click Here](https://docs.docker.com/desktop/install/windows-install/)

> For Download guide of `Docker Desktop` for <b>Linux</b>: [Click Here](https://docs.docker.com/desktop/install/linux-install/)

3. <b>Congratulations :sunglasses:, If you reach this step, you're just one step away from running 'Adaptive Image Code Gen LLM' on your local system </b>

    - Let's Press the trigger of an <b>LLM Application</b> by running below command:

    ```
    python3 main.py
    ```

<hr/>

## Future Work Enhancements:

1. We can add a new layer of `Image Verification` by integrating the **`LLaVa`** LLM Model. This model can verify the image with respect to its `Contexts` and `Prompts`, which will enhance the `Accuracy` of the current `WorkFlow`.

<hr/>

#### To Contribute to the Project:

1. Choose any open issue from [here](https://github.com/jaypatel15406/K8s-Control-Panel-Using-Streamlit/issues). 
2. Comment on the Issue: `Can I work on this?` and Start Exploring it.
3. Make changes to your Fork and Send a PR.

#### To Create a PR (Pull Request):

For Creating Valid PR Successfully. Kindly follow Guide: https://help.github.com/articles/creating-a-pull-request/

#### To Send a PR, Follow Rules Carefully !!   

**Otherwise your PR will be Closed**:

1. For Appropriate PR, follow Title Format: `Fixes #IssueNo : Name of the Issue`

For any Doubts related to the Issues, such as understanding Issue better etc., Comment Down your Queries on the Respective Issue.