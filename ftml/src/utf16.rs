/*
 * utf16.rs
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

use std::collections::HashMap;
use std::marker::PhantomData;

#[derive(Debug, Clone)]
pub struct Utf16IndexMap<'t> {
    /// A mapping of UTF-8 byte indices to UTF-16 indices, with the character.
    ///
    /// Schema: utf8_index -> utf16_index
    map: HashMap<usize, usize>,

    /// Borrow marker for the underlying string.
    ///
    /// This prevents this object from being valid if the underlying
    /// UTF-8 string is destructed.
    ///
    /// However since we don't actually need the string's contents,
    /// we use `PhantomData` here.
    marker: PhantomData<&'t str>,
}

impl<'t> Utf16IndexMap<'t> {
    /// Produces a mapping of UTF-8 byte index to UTF-16 index.
    ///
    /// This enables objects to be converted into using character indices
    /// for strings rather than byte indices. This is useful for environments
    /// which do use UTF-16 strings, such as Javascript (via WebASM).
    pub fn new(text: &'t str) -> Self {
        let mut map = HashMap::new();
        let mut utf16_index = 0;
        let mut last_utf8_index = None;

        // Add index for the start of each character
        for (utf8_index, ch) in text.char_indices() {
            map.insert(utf8_index, utf16_index);
            utf16_index += ch.len_utf16();
            last_utf8_index = Some(utf8_index + ch.len_utf8());
        }

        // Add last index, needed for the final token span.
        if let Some(utf8_index) = last_utf8_index {
            map.insert(utf8_index, utf16_index);
        }

        Utf16IndexMap {
            map,
            marker: PhantomData,
        }
    }

    /// Converts a UTF-8 byte index into a UTF-16 one.
    ///
    /// # Panics
    /// Panics if the index is out of range for the string,
    /// or the index is not on a UTF-8 byte boundary.
    #[inline]
    pub fn get_index(&self, utf8_index: usize) -> usize {
        self.map[&utf8_index]
    }
}