use std::borrow::Cow;

use super::prelude::*;
use regex::Regex;

lazy_static! {
    static ref WS_VARIABLE_REGEX: Regex = Regex::new(r"\{@(.+)\}").unwrap();
}

pub const RULE_WS_VARIABLE: Rule = Rule {
    name: "ws-variable",
    position: LineRequirement::Any,
    try_consume_fn,
};

fn try_consume_fn<'p, 'r, 't>(
    parser: &'p mut Parser<'r, 't>,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Consuming token by placing WikiScript variable contents");

    let ExtractedToken { slice, .. } = parser.current();

    let variable = WS_VARIABLE_REGEX
        .captures(slice)
        .expect("WikiScript Variable regex didn't match")
        .get(1)
        .expect("Capture group not found")
        .as_str();

    let value = parser.variable(Cow::from(variable));

    ok!(Element::Text(value))
}
