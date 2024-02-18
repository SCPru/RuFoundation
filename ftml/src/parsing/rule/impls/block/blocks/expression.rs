/*
 * parsing/rule/impls/block/blocks/image.rs
 *
 * ftml - Library to parse Wikidot text
 * Copyright (C) 2019-2022 Wikijump Team
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

use std::borrow::Cow;

use crate::data::ExpressionResult;

use super::prelude::*;

pub const BLOCK_IF: BlockRule = BlockRule {
    name: "block-if",
    accepts_names: &["#if", "#ifexpr"],
    accepts_star: false,
    accepts_score: false,
    accepts_newlines: false,
    accepts_partial: AcceptsPartial::None,
    parse_fn,
};

pub const BLOCK_IF_WITH_BODY: BlockRule = BlockRule {
    name: "block-if-body",
    accepts_names: &["if"],
    accepts_star: false,
    accepts_score: false,
    accepts_newlines: false,
    accepts_partial: AcceptsPartial::None,
    parse_fn: parse_if_with_body,
};

pub const BLOCK_IFEXPR_WITH_BODY: BlockRule = BlockRule {
    name: "block-ifexpr-body",
    accepts_names: &["ifexpr"],
    accepts_star: false,
    accepts_score: false,
    accepts_newlines: false,
    accepts_partial: AcceptsPartial::None,
    parse_fn: parse_ifexpr_with_body,
};

pub const BLOCK_EXPR: BlockRule = BlockRule {
    name: "block-expr",
    accepts_names: &["#expr"],
    accepts_star: false,
    accepts_score: false,
    accepts_newlines: false,
    accepts_partial: AcceptsPartial::None,
    parse_fn: parse_expr,
};

fn parse_fn<'r, 't>(
    parser: &mut Parser<'r, 't>,
    name: &'t str,
    flag_star: bool,
    flag_score: bool,
    in_head: bool,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Parsing expression block (name {name}, in-head {in_head})");
    assert!(!flag_star, "Expression doesn't allow star flag");
    assert!(!flag_score, "Expression doesn't allow score flag");

    // syntax: [[#if|#ifexpr condition | truthy nodes | falsey nodes]]

    let rule = parser.rule();

    let condition = collect_text(
        parser,
        rule,
        &[],
        &[ParseCondition::current(Token::Pipe)],
        &[],
        None,
    )?;

    let cond_matched =     
    match name.splitn(2, ':').next().unwrap_or("") {
        "#if" => evaluate_if(parser, condition),
        "#ifexpr" => evaluate_ifexpr(parser, condition),
        _ => unreachable!()
    };

    let parser_tx = &mut parser.transaction(ParserTransactionFlags::Footnotes | ParserTransactionFlags::TOC);

    let truthy_raw = collect_consume_keep(
        parser_tx,
        rule,
        &[],
        &[ParseCondition::current(Token::RightBlock), ParseCondition::current(Token::Pipe)],
        &[],
        None
    )?;

    let truthy = ParseSuccess::new(truthy_raw.item.0, truthy_raw.exceptions, truthy_raw.paragraph_safe);

    if cond_matched {
        parser_tx.commit();
    } else {
        parser_tx.rollback();
    }

    let falsey_tx = &mut parser_tx.transaction(ParserTransactionFlags::Footnotes | ParserTransactionFlags::TOC);

    let falsey = match truthy_raw.item.1.token {
        Token::Pipe => collect_consume(
            falsey_tx,
            rule,
            &[],
            &[ParseCondition::current(Token::RightBlock)],
            &[],
            None
        )?,
        Token::RightBlock => ParseSuccess::new(vec![], vec![], true),
        _ => return Err(falsey_tx.make_warn(ParseWarningKind::RuleFailed))
    };

    if !cond_matched {
        falsey_tx.commit();
    } else {
        falsey_tx.rollback();
    }

    // evaluate right away; 
    if cond_matched {
        ok!(truthy.paragraph_safe; truthy.item, truthy.exceptions)
    } else {
        ok!(truthy.paragraph_safe; falsey.item, truthy.exceptions)
    }
}

fn parse_if_with_body<'r, 't>(
    parser: &mut Parser<'r, 't>,
    name: &'t str,
    flag_star: bool,
    flag_score: bool,
    in_head: bool,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Parsing expression block (name {name}, in-head {in_head}; with body)");
    assert!(!flag_star, "Expression doesn't allow star flag");
    assert!(!flag_score, "Expression doesn't allow score flag");

    parse_with_body(parser, name, &BLOCK_IF_WITH_BODY)
}

fn parse_ifexpr_with_body<'r, 't>(
    parser: &mut Parser<'r, 't>,
    name: &'t str,
    flag_star: bool,
    flag_score: bool,
    in_head: bool,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Parsing expression block (name {name}, in-head {in_head}; with body)");
    assert!(!flag_star, "Expression doesn't allow star flag");
    assert!(!flag_score, "Expression doesn't allow score flag");

    parse_with_body(parser, name, &BLOCK_IFEXPR_WITH_BODY)
}

fn parse_with_body<'r, 't>(parser: &mut Parser<'r, 't>, name: &'t str, rule: &BlockRule) -> ParseResult<'r, 't, Elements<'t>> {
    // syntax: [[if|ifexpr condition]]truthy nodes[[else]]falsey nodes[[/if|ifexpr]]

    let condition = collect_text(
        parser,
        parser.rule(),
        &[],
        &[ParseCondition::current(Token::RightBlock)],
        &[],
        None,
    )?;

    let cond_matched =     
        match name.splitn(2, ':').next().unwrap_or("") {
            "if" => evaluate_if(parser, condition),
            "ifexpr" => evaluate_ifexpr(parser, condition),
            _ => unreachable!()
        };

    let parser_tx = &mut parser.transaction(ParserTransactionFlags::Footnotes | ParserTransactionFlags::TOC);

    // Get body content, never with paragraphs
    let (truthy, truthy_exceptions, _) =
        parser_tx.get_body_elements_with_custom_stop(rule, name, false, |parser| {
            // check for presence of "else"
            
            let found_else = parser.save_evaluate_fn(|parser| {
                let (name, _) = parser.get_block_name(false)?;

                if name == "else" {
                    Ok(true)
                } else {
                    Err(parser.make_warn(ParseWarningKind::ManualBreak))
                }
            });

            found_else.is_some()
        })?.into();

    let has_else = truthy_exceptions.iter().any(|exc| {
        match exc {
            ParseException::Warning(warning) => warning.kind() == ParseWarningKind::ManualBreak
        }
    });

    if cond_matched {
        parser_tx.commit();
    } else {
        parser_tx.rollback();
    }

    let falsey_tx = &mut parser_tx.transaction(ParserTransactionFlags::Footnotes | ParserTransactionFlags::TOC);

    let falsey = if has_else {
        let (falsey, _, _) = falsey_tx.get_body_elements(rule, name, false)?.into();

        falsey
    } else {
        vec![]
    };

    if !cond_matched {
        falsey_tx.commit();
    } else {
        falsey_tx.rollback();
    }

    //
    if cond_matched {
        ok!(true; truthy, vec![])
    } else {
        ok!(true; falsey, vec![])
    }
}

fn parse_expr<'r, 't>(
    parser: &mut Parser<'r, 't>,
    name: &'t str,
    flag_star: bool,
    flag_score: bool,
    in_head: bool,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Parsing expression block (name {name}, in-head {in_head})");
    assert!(!flag_star, "Expression doesn't allow star flag");
    assert!(!flag_score, "Expression doesn't allow score flag");

    // syntax: [[#expr expression]]

    let condition = collect_text(
        parser,
        parser.rule(),
        &[],
        &[ParseCondition::current(Token::RightBlock)],
        &[],
        None,
    )?;

    let result = evaluate_expr(parser, condition).to_string();

    ok!(Element::Text(Cow::from(result.to_owned())))
}

fn evaluate_if<'r, 't>(_parser: &mut Parser<'r, 't>, expr: &str) -> bool {
    let expr = expr.trim().to_ascii_lowercase();
    !(expr == "false" || expr == "null" || (expr.starts_with("{$") && expr.ends_with('}')) || (expr.starts_with("%%") && expr.ends_with("%%")))
}

fn evaluate_ifexpr<'r, 't>(parser: &mut Parser<'t, 't>, expr: &str) -> bool {
    match evaluate_expr(parser, expr) {
        ExpressionResult::Bool(b) => b,
        ExpressionResult::Int(i) => i != 0,
        ExpressionResult::Float(f) => f != 0.0,
        ExpressionResult::String(s) => s != "",
        ExpressionResult::None => false
    }
}

fn evaluate_expr<'r, 't>(parser: &mut Parser<'r, 't>, expr: &str) -> ExpressionResult<'static> {
    parser.page_callbacks().evaluate_expression(Cow::from(expr))
}