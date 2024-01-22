# Game-Stamina-Alarm

```mermaid
graph TB;
    subgraph PC;
    Client;
    end;
    subgraph Smartphone;
    Client-->Server;
    end;
    Server-->Condition["Check Stamina every 6 mins"];
    Condition-->|"not yet"|Server
```
