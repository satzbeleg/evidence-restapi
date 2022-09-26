import cassandra as cas
import cassandra.cluster
import cassandra.query
import cassandra.auth
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
            # reconnection_policy=cas.policies.ConstantReconnectionPolicy(
            #     1, None),
            # auth_provider=cas.auth.PlainTextAuthProvider(
            #     username=config_ev_cql["username"],
            #     password=config_ev_cql["password"])
        )
        # open an connection
        self.session = self.cluster.connect(
            wait_for_all_pools=False)
        # disable query timeout (`ResponseFuture.result()`, `cas.ReadTimeout`)
        self.session.default_timeout = None
        # set `USE keyspace;`
        self.session.set_keyspace(config_ev_cql["keyspace"])

    def get_session(self) -> cas.cluster.Session:
        return self.session

    def shutdown(self) -> None:
        self.session.shutdown()
        self.cluster.shutdown()
        gc.collect()
        pass
