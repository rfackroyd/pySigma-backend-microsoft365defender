from sigma.conversion.state import ConversionState
from sigma.processing.pipeline import ProcessingPipeline
from sigma.rule import SigmaRule
from sigma.conversion.base import TextQueryBackend
from sigma.conversion.deferred import DeferredQueryExpression
from sigma.conditions import ConditionItem, ConditionAND, ConditionOR, ConditionNOT, ConditionFieldEqualsValueExpression
from sigma.types import SigmaCompareExpression, SigmaString
from sigma.pipelines.microsoft365defender import microsoft_365_defender_pipeline
import sigma
import re
from typing import ClassVar, Dict, Tuple, Pattern, Any, Union


class Microsoft365DefenderBackend(TextQueryBackend):
    """Microsoft 365 Defender KQL Backend"""

    # Automatically apply pipeline
    backend_processing_pipeline: ClassVar[ProcessingPipeline] = microsoft_365_defender_pipeline()

    # The backend generates grouping if required
    name: ClassVar[str] = "Microsoft 365 Defender backend"
    formats: Dict[str, str] = {
        "default": "KQL for Microsoft 365 Defender Advanced Hunting queries",
    }

    requires_pipeline: bool = False  # m365 pipeline is automatically applied

    # Operator precedence
    precedence: ClassVar[Tuple[ConditionItem, ConditionItem, ConditionItem]] = (ConditionNOT, ConditionOR, ConditionAND)
    group_expression: ClassVar[
        str] = "({expr})"  # Expression for precedence override grouping as format string with {expr} placeholder

    # Generated query tokens
    token_separator: str = " "  # separator inserted between all boolean operators
    or_token: ClassVar[str] = "or"
    and_token: ClassVar[str] = "and"
    not_token: ClassVar[str] = " !~ "
    eq_token: ClassVar[str] = " =~ "  # Token inserted between field and value (without separator)

    # String output
    ## Fields
    ### Quoting
    field_quote: ClassVar[
        str] = "'"  # Character used to quote field characters if field_quote_pattern matches (or not, depending on field_quote_pattern_negation). No field name quoting is done if not set.
    field_quote_pattern: ClassVar[Pattern] = re.compile(
        "^\\w+$")  # Quote field names if this pattern (doesn't) matches, depending on field_quote_pattern_negation. Field name is always quoted if pattern is not set.
    field_quote_pattern_negation: ClassVar[
        bool] = True  # Negate field_quote_pattern result. Field name is quoted if pattern doesn't matches if set to True (default).

    ### Escaping
    field_escape: ClassVar[str] = ""  # Character to escape particular parts defined in field_escape_pattern.
    field_escape_quote: ClassVar[bool] = True  # Escape quote string defined in field_quote
    field_escape_pattern: ClassVar[Pattern] = re.compile(
        "\\s")  # All matches of this pattern are prepended with the string contained in field_escape.

    ## Values
    str_quote: ClassVar[str] = '"'  # string quoting character (added as escaping character)
    escape_char: ClassVar[str] = "\\"  # Escaping character for special characrers inside string
    wildcard_multi: ClassVar[str] = "*"  # Character used as multi-character wildcard
    wildcard_single: ClassVar[str] = "*"  # Character used as single-character wildcard
    add_escaped: ClassVar[str] = "\\"  # Characters quoted in addition to wildcards and string quote
    filter_chars: ClassVar[str] = ""  # Characters filtered
    bool_values: ClassVar[Dict[bool, str]] = {  # Values to which boolean values are mapped.
        True: "true",
        False: "false",
    }

    # String matching operators. if none is appropriate eq_token is used.
    startswith_expression: ClassVar[str] = "{field} startswith {value}"
    endswith_expression: ClassVar[str] = "{field} endswith {value}"
    contains_expression: ClassVar[str] = "{field} contains {value}"
    wildcard_match_expression: ClassVar[
        str] = "match"  # Special expression if wildcards can't be matched with the eq_token operator

    # Regular expressions
    re_expression: ClassVar[
        str] = "{field} matches regex \"{regex}\""  # Regular expression query as format string with placeholders {field} and {regex}
    re_escape_char: ClassVar[str] = "\\"  # Character used for escaping in regular expressions
    re_escape: ClassVar[Tuple[str]] = ()  # List of strings that are escaped
    re_escape_escape_char: bool = True  # If True, the escape character is also escaped

    # cidr expressions
    cidr_wildcard: ClassVar[str] = "*"  # Character used as single wildcard
    cidr_expression: ClassVar[
        str] = "ipv4_is_in_range({field}, \"{value}\")"  # CIDR expression query as format string with placeholders {field} = {value}
    cidr_in_list_expression: ClassVar[
        str] = "ipv4_is_in_any_range({field}, \"{value}\")"  # CIDR expression query as format string with placeholders {field} = in({list})

    # Numeric comparison operators
    compare_op_expression: ClassVar[
        str] = "{field} {operator} {value}"  # Compare operation query as format string with placeholders {field}, {operator} and {value}
    # Mapping between CompareOperators elements and strings used as replacement for {operator} in compare_op_expression
    compare_operators: ClassVar[Dict[SigmaCompareExpression.CompareOperators, str]] = {
        SigmaCompareExpression.CompareOperators.LT: "<",
        SigmaCompareExpression.CompareOperators.LTE: "<=",
        SigmaCompareExpression.CompareOperators.GT: ">",
        SigmaCompareExpression.CompareOperators.GTE: ">=",
    }

    # Null/None expressions
    field_null_expression: ClassVar[
        str] = "isnull({field})"  # Expression for field has null value as format string with {field} placeholder for field name

    # Field value in list, e.g. "field in (value list)" or "field containsall (value list)"
    convert_or_as_in: ClassVar[bool] = True  # Convert OR as in-expression
    convert_and_as_in: ClassVar[bool] = True  # Convert AND as in-expression
    in_expressions_allow_wildcards: ClassVar[
        bool] = True  # Values in list can contain wildcards. If set to False (default) only plain values are converted into in-expressions.
    field_in_list_expression: ClassVar[
        str] = "{field} {op} ({list})"  # Expression for field in list of values as format string with placeholders {field}, {op} and {list}
    or_in_operator: ClassVar[
        str] = "has_any"  # Operator used to convert OR into in-expressions. Must be set if convert_or_as_in is set
    and_in_operator: ClassVar[
        str] = "has_all"  # Operator used to convert AND into in-expressions. Must be set if convert_and_as_in is set
    list_separator: ClassVar[str] = ", "  # List element separator

    # Value not bound to a field
    unbound_value_str_expression: ClassVar[
        str] = '{value}'  # Expression for string value not bound to a field as format string with placeholder {value}
    unbound_value_num_expression: ClassVar[
        str] = '{value}'  # Expression for number value not bound to a field as format string with placeholder {value}
    unbound_value_re_expression: ClassVar[
        str] = '_=~{value}'  # Expression for regular expression not bound to a field as format string with placeholder {value}

    # Query finalization: appending and concatenating deferred query part
    deferred_start: ClassVar[str] = "\n| "  # String used as separator between main query and deferred parts
    deferred_separator: ClassVar[str] = "\n| "  # String used to join multiple deferred query parts
    deferred_only_query: ClassVar[str] = "*"  # String used as query if final query only contains deferred expression

    # TODO: implement custom methods for query elements not covered by the default backend base.
    # Documentation: https://sigmahq-pysigma.readthedocs.io/en/latest/Backends.html

    # We use =~ for eq_token so everything is case insensitive. But this cannot be used with ints/numbers in queries
    # So we can define a new token to use for SigmaNumeric types and override convert_condition_field_eq_val_num
    # to use it
    num_eq_token: ClassVar[str] = " == "

    # Override methods
    #  For numeric values, need == instead of =~
    def convert_condition_field_eq_val_num(self, cond: ConditionFieldEqualsValueExpression, state: ConversionState) -> \
            Union[str, DeferredQueryExpression]:
        """Conversion of field = number value expressions"""
        try:
            return self.escape_and_quote_field(cond.field) + self.num_eq_token + str(cond.value)
        except TypeError:  # pragma: no cover
            raise NotImplementedError("Field equals numeric value expressions are not supported by the backend.")

    def convert_condition_as_in_expression(self,
                                           cond: Union[ConditionOR, ConditionAND],
                                           state: ConversionState) -> Union[str, DeferredQueryExpression]:
        """Overridden method for conversion of field in value list conditions.
        KQL doesn't really use wildcards, so if we have an 'as_in' condition where one or more of the values has a wildcard,
        we can still use the as_in condition, then append on the wildcard value(s) with a startswith, endswith, or contains
        expression
        """

        field = self.escape_and_quote_field(cond.args[0].field)
        op1 = self.or_in_operator if isinstance(cond, ConditionOR) else self.and_in_operator
        op2 = self.or_token if isinstance(cond, ConditionOR) else self.and_token
        list_nonwildcard = self.list_separator.join([
            self.convert_value_str(arg.value, state)
            for arg in cond.args
            if (isinstance(arg.value, SigmaString) and not arg.value.contains_special()) or not isinstance(arg.value,
                                                                                                           SigmaString)
        ])
        list_wildcards = [
            arg.value for arg in cond.args if isinstance(arg.value, SigmaString) and arg.value.contains_special()
        ]
        as_in_expr = ""
        # Convert as_in and wildcard values separately
        if list_nonwildcard:
            as_in_expr = self.field_in_list_expression.format(
                field=field,
                op=op1,
                list=list_nonwildcard
            )
        wildcard_exprs_list = []
        if list_wildcards:
            for arg in list_wildcards:
                new_cond = ConditionFieldEqualsValueExpression(field=field, value=arg)
                expr = self.convert_condition_field_eq_val_str(new_cond, state)
                wildcard_exprs_list.append(expr)
        wildcard_exprs = f'{self.token_separator}{op2}{self.token_separator}'.join(wildcard_exprs_list)
        if as_in_expr and wildcard_exprs:
            return as_in_expr + self.token_separator + op2 + self.token_separator + wildcard_exprs
        return as_in_expr + wildcard_exprs

    def finalize_query_default(self, rule: SigmaRule, query: Any, index: int, state: ConversionState) -> Any:
        """
        Finalize conversion result of a query. The classes default behavior is to just return the query.
        We will add the table name to the beginning of the query based on the category of the rule.
        This is taken from the ProcessingPipeline state, which is why we automatically run the
        pipeline as part of the backend.
        """
        query_table = state.processing_state.get('query_table', None)
        query_table = query_table + "\n| where " if query_table else "search "

        return query_table + query
