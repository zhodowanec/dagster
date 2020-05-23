from dagster_graphql.test.sync_in_memory_run_launcher import SyncInMemoryRunLauncher

from dagster import DagsterInstance, seven
from dagster.core.host_representation import (
    EnvironmentHandle,
    ExternalRepository,
    InProcessOrigin,
    RepositoryHandle,
)
from dagster.core.test_utils import create_run_for_test

from .setup import create_main_recon_repo, define_repository


def test_sync_run_launcher_hijack_property():
    assert SyncInMemoryRunLauncher(False).hijack_start is False
    assert SyncInMemoryRunLauncher(True).hijack_start is True


def test_sync_run_launcher_from_configurable_class():
    with seven.TemporaryDirectory() as temp_dir:
        instance_no_hijack = DagsterInstance.local_temp(
            temp_dir,
            overrides={
                'run_launcher': {
                    'module': 'dagster_graphql.test.sync_in_memory_run_launcher',
                    'class': 'SyncInMemoryRunLauncher',
                    'config': {'hijack_start': False},
                }
            },
        )

        assert instance_no_hijack.run_launcher.hijack_start is False

    with seven.TemporaryDirectory() as temp_dir:
        instance_hijack = DagsterInstance.local_temp(
            temp_dir,
            overrides={
                'run_launcher': {
                    'module': 'dagster_graphql.test.sync_in_memory_run_launcher',
                    'class': 'SyncInMemoryRunLauncher',
                    'config': {'hijack_start': True},
                }
            },
        )

        assert instance_hijack.run_launcher.hijack_start is True


def test_sync_run_launcher_run():
    recon_repo = create_main_recon_repo()

    repository_handle = RepositoryHandle(
        repository_name='test',
        environment_handle=EnvironmentHandle(
            environment_name='test',
            in_process_origin=InProcessOrigin(recon_repo.pointer, repo_yaml=None),
        ),
    )

    external_repo = ExternalRepository.from_repository_def(define_repository(), repository_handle)
    external_pipeline = external_repo.get_full_external_pipeline('noop_pipeline')

    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(
            temp_dir,
            overrides={
                'run_launcher': {
                    'module': 'dagster_graphql.test.sync_in_memory_run_launcher',
                    'class': 'SyncInMemoryRunLauncher',
                    'config': {'hijack_start': False},
                }
            },
        )

        run = create_run_for_test(instance=instance, pipeline_name=external_pipeline.name)

        run = instance.run_launcher.launch_run(
            instance=instance, run=run, external_pipeline=external_pipeline
        )

        completed_run = instance.get_run_by_id(run.run_id)
        assert completed_run.is_success