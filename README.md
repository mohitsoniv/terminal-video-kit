# Terminal Video Kit

Terminal ki asli commands + Hindi narration + jis line ki baat ho rahi hai uska highlight = video.

## Ek baar ka setup
Tools chahiye: `vhs`, `ffmpeg`, `edge-tts`, `python3`, `script` (Ubuntu mein pehle se hota hai).

## Naya topic banane ka tareeka

1. Topic banao:
       ./new-topic.sh docker-basics
2. `topics/docker-basics/steps/` mein har step ki ek file banao: `01.cmd`, `02.cmd` ...
   - Har file mein **sirf ek command, ek line**.
   - Output aane mein 3 second se zyada lagta ho to upar likho: `# wait 6`
   - Kuch pehle se chalana ho (server, demo files) to `setup.sh` mein likho, band karna `cleanup.sh` mein.
3. Har command ek baar khud chalao aur output copy karo.
4. Neeche wala **template bhar ke Claude ko bhejo**. Claude `narration/01.txt`, `02.txt` ... dega.
5. Narration files `topics/docker-basics/narration/` mein rakho aur chalao:
       ./build.sh topics/docker-basics
   Video banegi: `topics/docker-basics/docker-basics.mp4`

## Claude ko bhejne ka template

    Terminal video kit ke liye narration chahiye.
    Topic: <jaise Docker basics>
    Audience: <beginner / senior review ke liye>
    Kya samjhana zaroori hai: <points>

    Step 01
    Command: <01.cmd ki command>
    Output:
    <poora output>

    Step 02
    Command: ...
    Output:
    ...

## Reset script: `steps/NN.pre` (optional)

Har command build ke dauraan 2 baar chalti hai. Agar command system ya data badalti hai (jaise `INSERT`,
`UPDATE`), to doosri baar output alag aayega. Iska hal: us step ke liye `steps/NN.pre` file banao —
ek bash script jo us step se pehle data ko sahi state mein la deti hai (table drop/create + seed).
Yeh chupchap chalti hai, video mein nahi dikhti. Example `topics/dbms-01-basics/steps/` mein hai.

## Narration file ka format

    # comment
    regex pattern ||| bolne wala sentence

- Pattern screen ki jis line se match karega, woh line us sentence ke dauraan highlight hogi.
- Pattern khaali chhodo to koi highlight nahi.
- Command wali line `$ ` se shuru hoti hai, isliye use `^\$ ` se pakdo.

## Rules (inke bina video toot sakti hai)

- **Har command build ke dauraan 2 baar dobara chalti hai** (VHS recording + highlight check). Isliye:
  - System badalne wali commands (`sudo`, `rm`, `apt`, `systemctl restart`, `kubectl delete`...) mat daalo. `build.sh` inhe rok deta hai. Pakka safe ho to `ALLOW_DANGEROUS=1 ./build.sh ...`
  - Kabhi khatam na hone wali commands (`top`, `vim`, `less`, `tail -f`, `watch`) nahi chalengi.
  - `sudo` password maangega aur build atak jayega.
- Output mein password, token, IP, hostname ho to video mein bhi aayega. Aisi commands demo/local data pe chalao.
- Screen pe lagbhag 25 lines aati hain. Isse lamba output ho to `| head -n 20` ya `| grep` lagao.

## Sirf patterns check karna (bina video banaye)

    bash topics/<naam>/setup.sh      # agar setup.sh hai
    python3 highlight.py check topics/<naam>
