/*
 * parsing/rule/impls/block/blocks/date.rs
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

use super::prelude::*;
use crate::tree::Date;
use chrono::prelude::*;
use regex::Regex;

pub const BLOCK_DATE: BlockRule = BlockRule {
    name: "block-date",
    accepts_names: &["date"],
    accepts_star: false,
    accepts_score: false,
    accepts_newlines: false,
    accepts_partial: AcceptsPartial::None,
    parse_fn,
};

fn parse_fn<'r, 't>(
    parser: &mut Parser<'r, 't>,
    name: &'t str,
    flag_star: bool,
    flag_score: bool,
    in_head: bool,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Parsing date block (name '{name}', in-head {in_head}, score {flag_score})");
    assert!(!flag_star, "Date doesn't allow star flag");
    assert!(!flag_score, "Date doesn't allow score flag");
    assert_block_name(&BLOCK_DATE, name);

    let (value, mut arguments) = parser.get_head_name_map(&BLOCK_DATE, in_head)?;
    let format = arguments.get("format");
    let arg_timezone = arguments.get("tz");
    let hover = arguments.get_bool(parser, "hover")?.unwrap_or(true);

    // Parse out timestamp given by user
    let mut date = parse_date(value)
        .map_err(|_| parser.make_warn(ParseWarningKind::BlockMalformedArguments))?;

    if let Some(arg) = arg_timezone {
        // Parse out argument timezone
        let offset = parse_timezone(&arg)
            .map_err(|_| parser.make_warn(ParseWarningKind::BlockMalformedArguments))?;

        // Add timezone. If None, then conflicting timezones.
        date = match date.add_timezone(offset) {
            Some(date) => date,
            None => {
                warn!(
                    "Date block has two specified timezones (argument {}, parsed {})",
                    arg.as_ref(),
                    offset,
                );

                return Err(parser.make_warn(ParseWarningKind::BlockMalformedArguments));
            }
        };
    }

    // Build and return element
    let element = Element::Date {
        value: date,
        format,
        hover,
    };

    ok!(element)
}

// Parser functions

/// Parse a datetime string and produce its time value, as well as possible timezone info.
fn parse_date(value: &str) -> Result<Date, DateParseError> {
    info!("Parsing possible date value '{value}'");

    // Special case, current time
    if value.eq_ignore_ascii_case("now") || value == "." {
        debug!("Was now");

        return Ok(now());
    }

    // Try UNIX timestamp (e.g. 1398763929)
    if let Ok(timestamp) = value.parse::<i64>() {
        debug!("Was UNIX timestamp '{timestamp}'");
        let date = NaiveDateTime::from_timestamp(timestamp, 0);
        return Ok(date.into());
    }

    // Try date strings
    if let Ok(date) = NaiveDate::parse_from_str(value, "%F") {
        debug!("Was ISO 8601 date string (dashes), result '{date}'");
        return Ok(date.into());
    }

    if let Ok(date) = NaiveDate::parse_from_str(value, "%Y/%m/%d") {
        debug!("Was ISO 8601 date string (slashes), result '{date}'");
        return Ok(date.into());
    }

    // Try datetime strings
    if let Ok(datetime) = NaiveDateTime::parse_from_str(value, "%FT%T") {
        debug!("Was ISO 8601 datetime string (dashes), result '{datetime}'");
        return Ok(datetime.into());
    }

    if let Ok(datetime) = NaiveDateTime::parse_from_str(value, "%Y/%m/%dT%T") {
        debug!("Was ISO 8601 datetime string (slashes), result '{datetime}'");
        return Ok(datetime.into());
    }

    // Try full RFC 3339 (stricter form of ISO 8601)
    if let Ok(datetime_tz) = DateTime::parse_from_rfc3339(value) {
        debug!("Was RFC 3339 datetime string, result '{datetime_tz}'");
        return Ok(datetime_tz.into());
    }

    // Exhausted all cases, failing
    Err(DateParseError)
}

/// Parse the timezone based on the specifier string.
fn parse_timezone(value: &str) -> Result<FixedOffset, DateParseError> {
    lazy_static! {
        static ref TIMEZONE_REGEX: Regex =
            Regex::new(r"^(\+|-)?([0-9]{1,2}):?([0-9]{2})?$").unwrap();
    }

    info!("Parsing possible timezone value '{value}'");

    // Try hours / minutes (via regex)
    if let Some(captures) = TIMEZONE_REGEX.captures(value) {
        // Get sign (+1 or -1)
        let sign = match captures.get(1) {
            None => 1,
            Some(mtch) => match mtch.as_str() {
                "+" => 1,
                "-" => -1,
                _ => unreachable!(),
            },
        };

        // Get hour value
        let hour = captures
            .get(2)
            .expect("No hour in timezone despite match")
            .as_str()
            .parse::<i32>()
            .expect("Hour wasn't integer despite match");

        // Get minute value
        let minute = match captures.get(3) {
            None => 0,
            Some(mtch) => mtch
                .as_str()
                .parse::<i32>()
                .expect("Minute wasn't integer despite match"),
        };

        // Get offset in seconds
        let seconds = sign * (hour * 3600 + minute * 60);

        debug!("Was offset via +HH:MM (sign {sign}, hour {hour}, minute {minute})");
        return Ok(FixedOffset::east(seconds));
    }

    // Try number of seconds
    //
    // This is lower-priority than the regex to permit "integer" cases,
    // such as "0800".
    if let Ok(seconds) = value.parse::<i32>() {
        debug!("Was offset in seconds ({seconds})");
        return Ok(FixedOffset::east(seconds));
    }

    // Exhausted all cases, failing
    Err(DateParseError)
}

#[derive(Debug, PartialEq, Eq)]
struct DateParseError;

#[inline]
fn now() -> Date {
    Utc::now().naive_utc().into()
}