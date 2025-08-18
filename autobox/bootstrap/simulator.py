import json
import uuid

from autobox.bootstrap.evaluator import prepare_evaluator
from autobox.bootstrap.metrics import generate
from autobox.bootstrap.orchestrator import prepare_orchestrator
from autobox.bootstrap.planner import prepare_planner
from autobox.bootstrap.reporter import prepare_reporter
from autobox.bootstrap.worker import prepare_workers
from autobox.core.messaging.broker import MessageBroker
from autobox.core.simulation import Simulation
from autobox.core.simulator import Simulator
from autobox.logging.logger import Logger
from autobox.schemas.config import Config


async def prepare_simulator(config: Config) -> Simulator:
    logger = Logger.get_instance()

    # orchestrator_config = config.simulation.orchestrator
    # simulation_name_id = value_to_id(config.simulation.name)

    logger.info("bootstrapping simulation...")

    orchestrator_id = str(uuid.uuid4())
    evaluator_id = str(uuid.uuid4())
    planner_id = str(uuid.uuid4())
    reporter_id = str(uuid.uuid4())
    worker_ids_by_name = {
        worker.name: str(uuid.uuid4()) for worker in config.simulation.workers
    }
    worker_names_by_id = {id: name for name, id in worker_ids_by_name.items()}

    logger.info(
        f"preparing meta-agents: orchestrator_id ({orchestrator_id}), evaluator_id ({evaluator_id}), planner_id ({planner_id}), reporter_id ({reporter_id})"
    )
    logger.info(f"preparing workers: {worker_ids_by_name}")

    message_broker = MessageBroker()

    workers = prepare_workers(config.simulation, message_broker, worker_ids_by_name)

    workers_info = json.dumps(
        [
            {"name": worker.name, "backstory": worker.backstory, "role": worker.role}
            for worker in workers
        ]
    )

    if config.metrics is None:
        metrics = generate(
            workers=workers_info,
            orchestrator_name=config.simulation.orchestrator.name,
            orchestrator_instruction=config.simulation.orchestrator.instruction,
            task=config.simulation.task,
        )
    else:
        metrics = config.metrics

    metrics_definitions = json.dumps(
        {metric.name: (metric.model_dump()) for metric in metrics}
    )

    evaluator = prepare_evaluator(
        id=evaluator_id,
        config=config.simulation,
        metrics=metrics_definitions,
        workers=workers_info,
        orchestrator_id=orchestrator_id,
        message_broker=message_broker,
    )

    planner = prepare_planner(
        id=planner_id,
        config=config.simulation,
        metrics=metrics_definitions,
        workers=workers_info,
        orchestrator_id=orchestrator_id,
        message_broker=message_broker,
    )

    reporter = prepare_reporter(
        id=reporter_id,
        config=config.simulation,
        metrics=metrics_definitions,
        orchestrator_id=orchestrator_id,
        message_broker=message_broker,
    )

    workers_memory = {worker.id: [] for worker in workers}

    simulation = Simulation(
        description=config.simulation.description,
        name=config.simulation.name,
        timeout=config.simulation.timeout_seconds,
        logger=logger,
        metrics=metrics,
    )

    orchestrator = prepare_orchestrator(
        config=config.simulation,
        metrics=metrics_definitions,
        id=orchestrator_id,
        evaluator_id=evaluator_id,
        worker_ids_by_name=worker_ids_by_name,
        worker_names_by_id=worker_names_by_id,
        workers_memory=workers_memory,
        planner_id=planner_id,
        reporter_id=reporter_id,
        message_broker=message_broker,
        simulation=simulation,
    )

    simulator = Simulator(
        description=config.simulation.description,
        name=config.simulation.name,
        timeout=config.simulation.timeout_seconds,
        logger=logger,
        metrics=metrics,
        workers=workers,
        orchestrator=orchestrator,
        evaluator=evaluator,
        planner=planner,
        reporter=reporter,
        message_broker=message_broker,
    )

    evaluator.simulation_id = simulation.id
    orchestrator.simulation_id = simulation.id
    logger.simulation_id = simulation.id

    # create_prometheus_metrics(metrics)
    # logger.info("Metrics loaded into Prometheus")
    # internal_dashboard_url, public_dashboard_url = await create_grafana_dashboard(
    #     simulation_name_id, simulation.id, metrics
    # )
    # simulation.internal_dashboard_url = internal_dashboard_url
    # simulation.public_dashboard_url = public_dashboard_url
    # logger.info(f"Dashboard URL: {internal_dashboard_url}")
    # logger.info(f"Public dashboard URL: {public_dashboard_url}")

    return simulator
