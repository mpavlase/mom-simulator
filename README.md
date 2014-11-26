MoM simulator
=========================
MoM is abbreviation of Memory overcommit Manager introduced by Adam Litke (aka aglitke on GitHub), currently as part of oVirt. This simulator will allow you feed MoM by prepared data (normally provided by collectors) and see result of utilization of your virtual 'host' and 'guests' in plot.

What it does
------------
According to input data simulate utilization of memory host and guests and watch how MoM will deal with this.


Quick how-to-use
-----------
Open terminal with content of this repo and type these commands.
This small utility will display output of visualization as plot. Script will end when you close window with plot, so open it in different terminal, or in background.
```
./mom/show_plot.py &
```

Now get things do something! Run MoM (as ordinary user) with updated config file. It will use **fakeHypervisor** driver and other _fake_ stuff to be able simulate MoM's behaviour.
```
./momd -c mom.fake.conf
```

During debugging simulator I add many log messages to be sure that all works correctly (hopefully). In ``` ./mom/hllog  ``` you can find colorizer (highlight log). Now you can see green INFO, red ERROR etc. and as addition hilighted given string. 
```
./momd -c mom.fake.conf |& ./mom/hllog 'Ballooning guest:'
```

What it doesn't?
----------------
Currently **fakeHypervisor** allows only host and guests memory management such as ballooning.
