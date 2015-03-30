We use stories to track the planning and implementation of features in this project. This page gives an overview of what is currently being done and how integrated features were implemented.

**Next story**: [story001](story001.md)

# Ongoing Iteration #

| **ID** | Est. | **Description** | **Assigned to** |
|:-------|:-----|:----------------|:----------------|
| [story000](story000.md) | 0 | Template for story pages | N/A |


## Timing symbols ##
```
1      - I evening or half-weekend-day of work to be spent.
10+    - story exceeds weekly time budged (should be broken down if possible)
10 (2) - multi iteration story (x) scheduled to be spend in advertised iteration
```

# Things to become stories #
_Some ideas from Thomas_
  * Add throughout test cases to existing code base. Since this is used to make investment decisions. It'll better be well validated.
  * Analyze data consistency problems that can occur during loading.
  * Formalize handling of semantic consistency changes (stock splits etc.). Since we will have to deal with it anyways, it'll better be formally defined and documented.
  * Unify EOD loaded to support other input data sources as well (Yahoo, Google Finance, ...)
  * Formalize interface of R-analysis programs to database. If we could hide this under a layer of abstraction, error handling could be much nicer done
  * Given the above, we should add error reporting and logging on all levels of the framework to be able to catch stuff.

## Long Term ##
  * CSV and SQLite may not scale well, it may be nice to add a "real" database backend. Something like Postgres or DB2-community. Python already provides a nice ORM layer for them using SQLAlchemy. I'm sure we could also easily find something to make it in R possible. In addition, pooling everything in a DB will provide major performance benefits when it comes to data integration across Python and R. Some of the existing analysis steps may then be possible to be pipelined.

# Completed Iterations #
N/A

# References #
  * ProjectDetails: back to starting page