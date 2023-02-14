import cassandra as cas
import cassandra.cluster
import cassandra.query
import cassandra.auth
import cassandra.policies
from .config import config_ev_cql
import gc


class CqlConn:
    def __init__(self):
        """ connect to Cassandra cluster """
        # connect to cluster
        self.cluster = cas.cluster.Cluster(
            contact_points=config_ev_cql["nodes"].split(","),
            port=config_ev_cql["port"],
            protocol_version=5,
            idle_heartbeat_interval=0,
            load_balancing_policy=cas.policies.RoundRobinPolicy(),
            reconnection_policy=cas.policies.ConstantReconnectionPolicy(
                delay=30., max_attempts=None),
            # auth_provider=cas.auth.PlainTextAuthProvider(
            #     username=config_ev_cql["username"],
            #     password=config_ev_cql["password"])
        )
        # open an connection
        self.session = self.cluster.connect(
            wait_for_all_pools=False)
        # disable query timeout (`ResponseFuture.result()`, `cas.ReadTimeout`)
        self.session.default_timeout = None
        # create keyspace and its tables IF NOT EXISTS
        _cas_init_tables(self.session, config_ev_cql["keyspace"], False)
        # set `USE keyspace;`
        self.session.set_keyspace(config_ev_cql["keyspace"])

    def get_session(self) -> cas.cluster.Session:
        return self.session

    def shutdown(self) -> None:
        self.session.shutdown()
        self.cluster.shutdown()
        gc.collect()
        pass


def _isvalid_keyspace_name(keyspace: str) -> bool:
    """ helper function for `_cas_init_tables` """
    try:
        if keyspace.islower():
            if keyspace.isalpha():
                return True
    except Exception:
        pass
    return False


def _cas_init_tables(session: cas.cluster.Session,
                     keyspace: str,
                     reset: bool = False) -> None:
    """ Initialize the CQL keyspace and tables for the new dataset.
        (only called in `CqlConn`)
    Parameters:
    -----------
    session : cas.cluster.Session
        A Cassandra Session object, i.e., an existing DB connection.
    keyspace : str
        The CQL KEYSPACE. Must be a string of lower case letters.
        Use the dataset name as keyspace.
    reset : bool (Default: False)
        Flag to delete and recreate the keyspace
    Notes:
    ------
    The `lemma` is used as partition key for `GROUP BY` and `WHERE` clauses,
    i.e., we can only query the whole data partion for a lemma.
    Parameters:
    -----------
    keyspace : str
        The CQL KEYSPACE. Must be a string of lower case letters.
        Use the dataset name as keyspace.
    reset : bool (Default False)
        Will drop keyspace in CQL
    """
    # check input arguments
    if not _isvalid_keyspace_name(keyspace):
        msg = (f"keyspace='{keyspace}' is not valid. "
               "Please use lower case letters")
        raise Exception(msg)

    # drop keyspace
    if reset:
        session.execute(f"DROP KEYSPACE IF EXISTS {keyspace};")

    # create a keyspace for the dataset
    session.execute(f"""
    CREATE KEYSPACE IF NOT EXISTS {keyspace}
    WITH REPLICATION = {{
        'class': 'SimpleStrategy',
        'replication_factor': 1
    }};
    """)

    # Table with pre-computed features
    # see: https://github.com/satzbeleg/evidence-features/blob/main/evidence_features/cql.py#L77
    session.execute(f"""
    CREATE TABLE IF NOT EXISTS {keyspace}.tbl_features (
      headword  TEXT
    , example_id UUID
    , sentence  TEXT
    , sent_id   UUID
    , spans    frozen<list<frozen<list<SMALLINT>>>>
    , annot    TEXT
    , biblio   TEXT
    , license  TEXT
    , score    FLOAT
    , feats1   frozen<list<TINYINT>>
    , feats2   frozen<list<TINYINT>>
    , feats3   frozen<list<TINYINT>>
    , feats4   frozen<list<TINYINT>>
    , feats5   frozen<list<SMALLINT>>
    , feats6   frozen<list<SMALLINT>>
    , feats7   frozen<list<SMALLINT>>
    , feats8   frozen<list<TINYINT>>
    , feats9   frozen<list<TINYINT>>
    , feats12  frozen<list<SMALLINT>>
    , feats13  frozen<list<TINYINT>>
    , feats14  frozen<list<TINYINT>>
    , hashes15  frozen<list<INT>>
    , hashes16  frozen<list<INT>>
    , hashes18  frozen<list<INT>>
    , PRIMARY KEY ((headword), sentence)
    );
    """)

    # Table for BWS-rankings annotated via the Web-App
    session.execute(f"""
    CREATE TABLE IF NOT EXISTS {keyspace}.evaluated_bestworst (
      set_id  UUID
    , user_id UUID
    , ui_name TEXT
    , headword          TEXT
    , event_history     TEXT
    , state_sentid_map  TEXT
    , tracking_data     TEXT
    , PRIMARY KEY(headword, set_id)
    );
    """)

    # Table for the interactivity convergence data
    session.execute(f"""
    CREATE TABLE IF NOT EXISTS {keyspace}.interactivity_convergence (
      episode_id  UUID
    , training_score_history  frozen<list<FLOAT>>
    , model_score_history     frozen<list<FLOAT>>
    , displayed               frozen<list<TINYINT>>
    , user_id       UUID
    , sentence_text TEXT
    , headword      TEXT
    , PRIMARY KEY(headword, sentence_text, episode_id)
    );
    """)
    pass
