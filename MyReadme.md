# Alice & Bob - Python coding assessment

Here is my assessment for the Python test and a little explanation of what I did.
As requested, you need to launch the command

```shell
python3 run.py 3,input1,output1 5,input2,output2
```

to compute the moving averages in the files output1 and output2. 
You can also first run this command and only after use the datastream command. The python process will remain until all the input have been read. 
If you want to stop it after a certain time, you can add an option -t (or --time) with the amount in seconds like this : 

```shell
python3 run.py -t 10 3,input1,output1 5,input2,output2
```
In this case, the Python script will be run for 10 seconds.

You can also decide to have a verbose mode in order to see what is being processed. In this case, the option -v (or --verbose) will do the job : 

```shell
python3 run.py -v 3,input1,output1 5,input2,output2
```
