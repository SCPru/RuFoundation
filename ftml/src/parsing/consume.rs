/*
 * parsing/consume.rs
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

//! Module for look-ahead checking.
//!
//! This contains implementations of eager functions that try to interpret the
//! upcoming tokens as a particular object (e.g. seeing a `[[` and you see if it's a module).
//!
//! The parser is not disambiguous because any string of tokens can be interpreted
//! as raw text as a fallback, which is how Wikidot does it.

use super::prelude::*;
use super::rule::{get_rules_for_token, impls::RULE_FALLBACK};
use super::Parser;
use std::mem;

/// Main function that consumes tokens to produce a single element, then returns.
///
/// It will use the fallback if all rules, fail, so the only failure case is if
/// the end of the input is reached.
pub fn consume<'p, 'r, 't>(
    parser: &'p mut Parser<'r, 't>,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!(
        "Running consume attempt (token {}, slice {:?})",
        parser.current().token.name(),
        parser.current().slice,
    );

    // Incrementing recursion depth
    // Will fail if we're too many layers in
    parser.depth_increment()?;

    debug!("Looking for valid rules");
    let mut all_exceptions = Vec::new();
    let current = parser.current();

    // check if this node is cached
    let this_pos = current.span.start;
    let step_orig = parser.remaining().len();
    match parser.cached_node(this_pos) {
        Some((consumed_tokens, result)) => {
            parser.step_n(consumed_tokens)?;
            parser.depth_decrement();
            return Ok(result);
        }
        None => {}
    }

    for &rule in get_rules_for_token(current) {
        debug!("Trying rule consumption for tokens (rule {})", rule.name());

        let old_remaining = parser.remaining();

        match rule.try_consume(parser) {
            Ok(output) => {
                info!("Rule {} matched, returning generated result", rule.name());

                // If the pointer hasn't moved, we step one token.
                if parser.same_pointer(old_remaining) {
                    parser.step()?;
                }

                // Explicitly drop exceptions
                //
                // We're returning the successful consumption
                // so these are going to be dropped as a previously
                // unsuccessful attempts.
                mem::drop(all_exceptions);

                // Decrement recursion depth
                parser.depth_decrement();

                // Store to cache
                // Avoid caching InputStart, InputEnd or other possible null tokens; this breaks cache
                // Avoid caching partials because they depend on the _real_ context
                if current.span.start != current.span.end && !output.has_partials() {
                    parser.put_cached_node(this_pos, step_orig - parser.remaining().len(), output.to_owned());
                }

                return Ok(output);
            }
            Err(warning) => {
                warn!(
                    "Rule failed, returning warning: '{}'",
                    warning.kind().name(),
                );
                all_exceptions.push(ParseException::Warning(warning));
            }
        }
    }

    warn!("All rules exhausted, using generic text fallback");
    let element = text!(current.slice);
    parser.step()?;

    // We should only carry styles over from *successful* consumptions
    debug!("Removing non-warnings from exceptions list");
    all_exceptions.retain(|exception| matches!(exception, ParseException::Warning(_)));

    let mut is_partial_error = false;
    // If we've hit the recursion limit, just bail
    // If the error was caused by presence of unexpected partials, do not cache it; this partial might be valid in other context
    if let Some(ParseException::Warning(warning)) = all_exceptions.first() {
        match warning.kind() {
            ParseWarningKind::RecursionDepthExceeded => {
                error!("Found recursion depth error, failing");
                return Err(warning.clone());
            }
            ParseWarningKind::ListItemOutsideList
            |ParseWarningKind::TableRowOutsideTable
            |ParseWarningKind::TableCellOutsideTable
            |ParseWarningKind::TabOutsideTabView
            |ParseWarningKind::RubyTextOutsideRuby => {
                is_partial_error = true;
            }
            _ => {}
        }
    }
    
    // Add fallback warning to exceptions list
    all_exceptions.push(ParseException::Warning(ParseWarning::new(
        ParseWarningKind::NoRulesMatch,
        RULE_FALLBACK,
        current,
    )));

    // Decrement recursion depth
    parser.depth_decrement();

    let failure_output = ok!(element, all_exceptions);

    // Store text node to cache as well; this is the most important part so that we know to not re-parse failed nodes
    // Avoid caching InputStart, InputEnd or other possible null tokens; this breaks cache
    if current.span.start != current.span.end && !is_partial_error {
        parser.put_cached_node(this_pos, step_orig - parser.remaining().len(), failure_output.clone().unwrap());
    }

    failure_output
}
