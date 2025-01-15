from auditlog_extra.graphene_decorators import auditlog_access
from tests.models import DummyTestModel


class DjangoObjectType:
    """
    Mimic Django Graphene DjangoObjectType for test use,
    because there is  no hard dependency to Graphene.
    """

    @classmethod
    def get_node(cls, info, id):
        return DummyTestModel(text_field="text", number_field=1, boolean_field=True)


class TestModelType(DjangoObjectType):
    class Meta:
        model = DummyTestModel
        fields = ("text_field", "number_field", "boolean_field")


@auditlog_access
class LoggedTestModelType(DjangoObjectType):
    class Meta:
        model = DummyTestModel
        fields = ("text_field", "number_field", "boolean_field")


class Query:
    @staticmethod
    def resolve_test_model(root, info, id):
        return TestModelType.get_node(info, id)

    @staticmethod
    def resolve_logged_test_model(root, info, id):
        return LoggedTestModelType.get_node(info, id)
