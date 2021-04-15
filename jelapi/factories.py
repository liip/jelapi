import factory
from faker_enum import EnumProvider

from tests.utils import get_standard_env

from . import classes

factory.Faker.add_provider(provider=EnumProvider)


class _JelasticEnvironmentFactory(factory.Factory):
    class Meta:
        model = classes.JelasticEnvironment

    jelastic_env = get_standard_env()


class _JelasticNodeGroupFactory(factory.Factory):
    class Meta:
        model = classes.JelasticNodeGroup

    parent = _JelasticEnvironmentFactory()
    nodeGroup = factory.Faker("enum", enum_cls=classes.JelasticNodeGroup.NodeGroupType)
    nodeType = factory.Faker("enum", enum_cls=classes.JelasticNode.NodeType)


class JelasticNodeFactory(factory.Factory):
    class Meta:
        model = classes.JelasticNode

    node_group = _JelasticNodeGroupFactory()
    nodeType = factory.Faker("enum", enum_cls=classes.JelasticNode.NodeType)


class JelasticEnvironmentFactory(_JelasticEnvironmentFactory):
    @classmethod
    def _after_postgeneration(obj, instance, create, results=None):
        """
        Generate a standard Env
        """
        instance.nodeGroups = {
            "cp": JelasticNodeGroupFactory(
                parent=instance,
                nodeGroup=classes.JelasticNodeGroup.NodeGroupType.APPLICATION_SERVER,
                nodeType=classes.JelasticNode.NodeType.DOCKER,
            ),
            "sqldb": JelasticNodeGroupFactory(
                parent=instance,
                nodeGroup=classes.JelasticNodeGroup.NodeGroupType.SQL_DATABASE,
                nodeType=classes.JelasticNode.NodeType.DOCKER,
            ),
            "storage": JelasticNodeGroupFactory(
                parent=instance,
                nodeGroup=classes.JelasticNodeGroup.NodeGroupType.STORAGE_CONTAINER,
                nodeType=classes.JelasticNode.NodeType.STORAGE,
            ),
        }


class JelasticNodeGroupFactory(_JelasticNodeGroupFactory):
    @classmethod
    def _after_postgeneration(obj, instance, create, results=None):
        """
        Generate a standard Env
        """
        instance.nodes = [JelasticNodeFactory(node_group=instance)]
